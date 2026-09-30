// Durable Object (SQLite storage) holding the rolling price window, cooldowns and the
// daily universe/baseline job. One instance ("global"). Writes per scan: one snapshot row
// plus one delete, so ~2,900 rows written/day, far inside the free plan's 100,000.
import { DurableObject } from "cloudflare:workers";
import { RULES } from "./config";
import type { Env } from "./config";
import type { UniverseEntry } from "./exchanges";

export interface Job {
  phase: "kraken_pairs" | "kraken_ticker" | "coinbase" | "baseline" | "publish" | "done";
  startedAt: number;
  krakenPairs?: Record<string, string>;
  kraken?: UniverseEntry[];
  coinbase?: UniverseEntry[];
  cbOffset?: number;
  universe?: UniverseEntry[];
  cursor?: number;
  baseline?: Record<string, number>;
  failed?: string[];      // bases whose daily candles failed (e.g. 429); retried once before publishing
  retried?: boolean;
}

export interface TickResult {
  ago: Record<string, number> | null;   // prices from the snapshot closest to 30 min ago
  agoTs: number | null;
  agoEarly: Record<string, number> | null;   // same, ~15 min ago (early-warning window)
  cooldown: Record<string, number>;     // key -> last alert ms (base for spikes, "early:" + base for early alerts)
}

export class SpikeState extends DurableObject<Env> {
  sql: SqlStorage;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(`CREATE TABLE IF NOT EXISTS snapshots (ts INTEGER PRIMARY KEY, prices TEXT NOT NULL)`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS cooldown (base TEXT PRIMARY KEY, ts INTEGER NOT NULL)`);
  }

  /** Store this minute's prices; return the snapshots closest to 30 and 15 min ago (±2 min) and
   *  active cooldowns. */
  async tick(ts: number, prices: Record<string, number>): Promise<TickResult> {
    this.sql.exec(`INSERT OR REPLACE INTO snapshots (ts, prices) VALUES (?, ?)`, ts, JSON.stringify(prices));
    this.sql.exec(`DELETE FROM snapshots WHERE ts < ?`, ts - 40 * 60_000);
    const near = (min: number) => {
      const target = ts - min * 60_000;
      return this.sql.exec<{ ts: number; prices: string }>(
        `SELECT ts, prices FROM snapshots WHERE ts BETWEEN ? AND ? ORDER BY ABS(ts - ?) LIMIT 1`,
        target - 2 * 60_000, target + 2 * 60_000, target).toArray()[0];
    };
    const row = near(RULES.windowMin), early = near(RULES.early.windowMin);
    const cooldown: Record<string, number> = {};
    const since = ts - Math.max(RULES.cooldownMs, RULES.early.cooldownMs);
    for (const r of this.sql.exec<{ base: string; ts: number }>(`SELECT base, ts FROM cooldown WHERE ts > ?`, since))
      cooldown[r.base] = r.ts;
    return {
      ago: row ? JSON.parse(row.prices) : null, agoTs: row ? row.ts : null,
      agoEarly: early ? JSON.parse(early.prices) : null, cooldown,
    };
  }

  /** key: the base symbol for a spike alert, "early:" + base for an early alert. */
  async markAlert(key: string, ts: number): Promise<void> {
    this.sql.exec(`INSERT OR REPLACE INTO cooldown (base, ts) VALUES (?, ?)`, key, ts);
  }

  async getJob(): Promise<Job | null> {
    return (await this.ctx.storage.get<Job>("job")) ?? null;
  }

  async setJob(job: Job): Promise<void> {
    await this.ctx.storage.put("job", job);
  }
}
