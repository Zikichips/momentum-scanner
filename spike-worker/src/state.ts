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
  cooldown: Record<string, number>;     // base -> last alert ms, within the cooldown window
}

export class SpikeState extends DurableObject<Env> {
  sql: SqlStorage;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(`CREATE TABLE IF NOT EXISTS snapshots (ts INTEGER PRIMARY KEY, prices TEXT NOT NULL)`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS cooldown (base TEXT PRIMARY KEY, ts INTEGER NOT NULL)`);
  }

  /** Store this minute's prices; return the ~30-min-ago snapshot (28–32 min back) and active cooldowns. */
  async tick(ts: number, prices: Record<string, number>): Promise<TickResult> {
    this.sql.exec(`INSERT OR REPLACE INTO snapshots (ts, prices) VALUES (?, ?)`, ts, JSON.stringify(prices));
    this.sql.exec(`DELETE FROM snapshots WHERE ts < ?`, ts - 40 * 60_000);
    const target = ts - RULES.windowMin * 60_000;
    const rows = this.sql.exec<{ ts: number; prices: string }>(
      `SELECT ts, prices FROM snapshots WHERE ts BETWEEN ? AND ? ORDER BY ABS(ts - ?) LIMIT 1`,
      target - 2 * 60_000, target + 2 * 60_000, target).toArray();
    const cooldown: Record<string, number> = {};
    for (const r of this.sql.exec<{ base: string; ts: number }>(`SELECT base, ts FROM cooldown WHERE ts > ?`, ts - RULES.cooldownMs))
      cooldown[r.base] = r.ts;
    return { ago: rows.length ? JSON.parse(rows[0].prices) : null, agoTs: rows.length ? rows[0].ts : null, cooldown };
  }

  async markAlert(base: string, ts: number): Promise<void> {
    this.sql.exec(`INSERT OR REPLACE INTO cooldown (base, ts) VALUES (?, ?)`, base, ts);
  }

  async getJob(): Promise<Job | null> {
    return (await this.ctx.storage.get<Job>("job")) ?? null;
  }

  async setJob(job: Job): Promise<void> {
    await this.ctx.storage.put("job", job);
  }
}
