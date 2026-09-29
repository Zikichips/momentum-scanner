// Spike detector. Detection and measurement only: it alerts and grades, it never trades.
//   * * * * *     scan       — quotes for the universe, rolling window, spike check, alert
//   */10 * * * *  grade      — fill ret_15/30/60/240, MFE/MAE, TP/stop-first for recent alerts
//   0 4 * * *     baseline   — start the universe + 30-day baseline rebuild; write the scoreboard
// The rebuild is split into one bounded step per scan tick (CPU and subrequest limits), and
// publishes the universe and baseline to KV once, when complete.
import { BUDGET, RULES } from "./config";
import type { Env } from "./config";
import {
  COINBASE_PAGE, fetchCandles, fetchCoinbasePage, fetchKrakenPairs, fetchKrakenTickerAll, fetchQuotes, mergeUniverse,
  type UniverseEntry,
} from "./exchanges";
import { evaluateSpike, formatAlert, gradePath, levels, liquidityLabel, positionSize, scoreboard, type GradedRow } from "./rules";
import { hasSupabase, newsHeadline, priorSpikes, redditMentions, sb, telegram } from "./services";
import type { Job } from "./state";

export { SpikeState } from "./state";

const KV_UNIVERSE = "universe";
const KV_BASELINE = "baseline";

const state = (env: Env) => env.SPIKE_STATE.get(env.SPIKE_STATE.idFromName("global"));

export default {
  async scheduled(event: ScheduledController, env: Env, ctx: ExecutionContext) {
    const now = event.scheduledTime;
    if (event.cron === "*/10 * * * *") return grade(env, now);
    if (event.cron === "0 4 * * *") return baselineCron(env, now);
    return scan(env, now);
  },

  async fetch(req: Request, env: Env): Promise<Response> {
    // Read-only status for local dev and checks after deploy.
    if (new URL(req.url).pathname === "/status") {
      const [u, b, job] = await Promise.all([
        env.SPIKE_KV.get<any>(KV_UNIVERSE, "json"), env.SPIKE_KV.get<any>(KV_BASELINE, "json"), state(env).getJob(),
      ]);
      return Response.json({
        universe: u ? { built_at: u.built_at, size: u.entries.length, top: u.entries.slice(0, 5) } : null,
        baseline: b ? { built_at: b.built_at, symbols: Object.keys(b.avg_daily_volume).length } : null,
        job: job ? { phase: job.phase, startedAt: new Date(job.startedAt).toISOString(), cursor: job.cursor } : null,
      });
    }
    return new Response("spike-detector: see /status", { status: 404 });
  },
};

// ------------------------------------------------------------------ scan (every minute)
async function scan(env: Env, now: number) {
  const [u, b] = await Promise.all([
    env.SPIKE_KV.get<{ entries: UniverseEntry[] }>(KV_UNIVERSE, "json"),
    env.SPIKE_KV.get<{ avg_daily_volume: Record<string, number> }>(KV_BASELINE, "json"),
  ]);
  const st = state(env);
  if (!u || !b) {
    // First run (or KV lost): build the universe before scanning.
    const job = await st.getJob();
    if (!job || job.phase === "done") await st.setJob({ phase: "kraken_pairs", startedAt: now });
    await baselineStep(env, now);
    return;
  }

  const quotes = await fetchQuotes(u.entries);
  const prices = Object.fromEntries(Object.entries(quotes).map(([k, q]) => [k, q.price]));
  const { ago, agoTs, cooldown } = await st.tick(now, prices);
  console.log(`scan ${new Date(now).toISOString()}: ${Object.keys(quotes).length}/${u.entries.length} quotes, ` +
              (agoTs ? `window from ${Math.round((now - agoTs) / 60_000)} min ago` : "no 30-min-old snapshot yet"));

  if (ago) {
    const byBase = new Map(u.entries.map(e => [e.base, e]));
    const candidates = Object.entries(quotes)
      .filter(([base, q]) => q.qvol24 >= RULES.minQuoteVolume24h && ago[base] > 0 && !cooldown[base]
                              && q.price / ago[base] - 1 >= RULES.prefilterMove)
      .sort((x, y) => y[1].price / ago[y[0]] - x[1].price / ago[x[0]])
      .slice(0, BUDGET.maxCandidatesPerScan);

    let alerts = 0;
    for (const [base, q] of candidates) {
      if (alerts >= BUDGET.maxAlertsPerScan) break;
      const e = byBase.get(base)!;
      try {
        const candles = await fetchCandles(e, 1, now - (RULES.windowMin + 1) * 60_000);
        const chk = evaluateSpike(candles, q.price, b.avg_daily_volume[base], now);
        console.log(`candidate ${base} ${e.exchange}: ${chk.ok ? "SPIKE" : chk.reasons.join(", ")}`);
        if (!chk.ok) continue;
        await fireAlert(env, e, q, chk, now);
        await st.markAlert(base, now);
        alerts++;
      } catch (err) {
        console.log(`candidate ${base}: ${err}`);
      }
    }
  }

  await baselineStep(env, now);   // no-op unless the daily rebuild is running
}

async function fireAlert(env: Env, e: UniverseEntry, q: { price: number; qvol24: number },
                         chk: ReturnType<typeof evaluateSpike>, now: number) {
  const lv = levels(q.price, chk.priceAgo);
  const size = positionSize(q.price, lv.stop, +env.CAPITAL_USD, +env.RISK_PCT, +env.MAX_POSITION_PCT);
  const [hourly, news, reddit, prior] = await Promise.all([
    fetchCandles(e, 60, now - (7 * 24 + 2) * 3600_000).catch(() => []),
    newsHeadline(env, e.base, now),
    redditMentions(env, e.base, now),
    priorSpikes(env, e.base, now),
  ]);
  const closeAt = (msAgo: number) => {
    const t = now - msAgo;
    const bar = [...hourly].reverse().find(c => c.t <= t);
    return bar ? bar.close : null;
  };
  const c24 = closeAt(24 * 3600_000), c7 = closeAt(7 * 24 * 3600_000);
  const liquidity = liquidityLabel(q.qvol24);

  const text = formatAlert({
    symbol: e.base, exchange: e.exchange, move30: chk.move, volMultiple: chk.volMultiple, price: q.price, high: chk.high,
    chg24h: c24 ? (q.price / c24 - 1) * 100 : null, chg7d: c7 ? (q.price / c7 - 1) * 100 : null,
    liquidity, vol24h: q.qvol24, headline: news.headline, reddit, prior, size, lv,
  });

  const row = {
    symbol: e.base, exchange: e.exchange, pair_id: e.id, fired_at: new Date(now).toISOString(),
    price_at_alert: q.price, price_30m_ago: chk.priceAgo, high_30m: chk.high,
    move_30m: Math.round(chk.move * 100_000) / 1000, vol_multiple: Math.round(chk.volMultiple * 100) / 100,
    liquidity_label: liquidity, vol_24h: Math.round(q.qvol24),
    has_news: news.checked ? news.headline != null : null, news_headline: news.headline,
    reddit_ratio: reddit && reddit.avg7d > 0 ? Math.round(reddit.m24 / reddit.avg7d * 100) / 100 : null,
    prior_spikes_90d: prior.n, size_usd: size, stop: lv.stop, take_profit: lv.takeProfit,
  };
  if (hasSupabase(env)) {
    await sb(env, "spike_alerts", { method: "POST", body: JSON.stringify(row), headers: { Prefer: "return=minimal" } })
      .catch(err => console.log("store alert failed:", String(err)));
  } else {
    console.log("[supabase disabled] alert row", JSON.stringify(row));
  }
  await telegram(env, text);
}

// ------------------------------------------------------------------ grade (every 10 minutes)
async function grade(env: Env, now: number) {
  if (!hasSupabase(env)) return console.log("[supabase disabled] nothing to grade");
  const ready = new Date(now - 15 * 60_000).toISOString();
  const rows: any[] = await sb(env,
    `spike_alerts?graded_complete=eq.false&fired_at=lt.${ready}&order=fired_at.asc&limit=${BUDGET.maxGradesPerRun}` +
    `&select=id,exchange,pair_id,fired_at,price_at_alert,stop,take_profit`);
  for (const r of rows) {
    try {
      const firedAt = Date.parse(r.fired_at);
      const candles = await fetchCandles({ exchange: r.exchange, id: r.pair_id }, 1, firedAt);
      const patch = gradePath({ firedAt, price: r.price_at_alert, stop: r.stop, takeProfit: r.take_profit }, candles, now);
      await sb(env, `spike_alerts?id=eq.${r.id}`, {
        method: "PATCH", body: JSON.stringify({ ...patch, graded_at: new Date(now).toISOString() }),
        headers: { Prefer: "return=minimal" },
      });
    } catch (err) {
      console.log(`grade ${r.id}: ${err}`);
    }
  }
  console.log(`graded ${rows.length}`);
}

// ------------------------------------------------------------------ baseline (daily) + scoreboard
async function baselineCron(env: Env, now: number) {
  await state(env).setJob({ phase: "kraken_pairs", startedAt: now });
  await baselineStep(env, now);
  if (hasSupabase(env)) {
    const rows: GradedRow[] = await sb(env,
      "spike_alerts?graded_complete=eq.true&select=liquidity_label,has_news,ret_15,ret_30,ret_60,ret_240,net_60,hit_tp_first,hit_stop_first");
    const day = new Date(now).toISOString().slice(0, 10);
    await sb(env, "spike_scoreboard?on_conflict=day,segment", {
      method: "POST", body: JSON.stringify(scoreboard(day, rows)),
      headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
    });
    console.log(`scoreboard ${day}: ${rows.length} graded alerts`);
  }
}

/** One bounded step of the universe + baseline rebuild. Each step parses at most one large payload. */
async function baselineStep(env: Env, now: number) {
  const st = state(env);
  const job = await st.getJob();
  if (!job || job.phase === "done") return;
  const next = async (patch: Partial<Job>) => st.setJob({ ...job, ...patch });

  switch (job.phase) {
    case "kraken_pairs":
      return next({ phase: "kraken_ticker", krakenPairs: await fetchKrakenPairs() });
    case "kraken_ticker":
      return next({ phase: "coinbase", kraken: await fetchKrakenTickerAll(job.krakenPairs!), krakenPairs: undefined, cbOffset: 0 });
    case "coinbase": {
      const { entries, last } = await fetchCoinbasePage(job.cbOffset!);
      const coinbase = [...(job.coinbase ?? []), ...entries];
      if (!last) return next({ coinbase, cbOffset: job.cbOffset! + COINBASE_PAGE });
      const universe = mergeUniverse(job.kraken!, coinbase, RULES.universeSize);
      return next({ phase: "baseline", universe, kraken: undefined, coinbase: undefined, cursor: 0, baseline: {} });
    }
    case "baseline": {
      // Main pass over the universe, then one retry pass over failures (Coinbase sometimes
      // returns 429 to Cloudflare's shared egress IPs). Fetches run one at a time to avoid bursts.
      const universe = job.universe!, baseline = { ...job.baseline }, failed = [...(job.failed ?? [])];
      const list = job.retried ? universe.filter(e => failed.includes(e.base)) : universe;
      const batch = list.slice(job.cursor!, job.cursor! + BUDGET.baselineFetchesPerTick);
      const dayStart = Math.floor(now / 86_400_000) * 86_400_000;
      for (const e of batch) {
        try {
          const days = (await fetchCandles(e, 1440, dayStart - (RULES.baselineDays + 1) * 86_400_000))
            .filter(c => c.t < dayStart)                       // complete days only
            .slice(-RULES.baselineDays);
          if (days.length >= RULES.minBaselineDays) baseline[e.base] = days.reduce((s, c) => s + c.volume, 0) / days.length;
          if (job.retried) failed.splice(failed.indexOf(e.base), 1);
        } catch (err) {
          console.log(`baseline ${e.base}${job.retried ? " (retry)" : ""}: ${err}`);
          if (!job.retried) failed.push(e.base);
        }
      }
      const cursor = job.cursor! + batch.length;
      if (cursor < list.length) return next({ cursor, baseline, failed });
      if (!job.retried && failed.length) return next({ cursor: 0, baseline, failed, retried: true });
      if (failed.length) console.log(`baseline missing after retry: ${failed.join(", ")}`);
      return next({ baseline, failed, phase: "publish" });
    }
    case "publish": {
      const built_at = new Date(now).toISOString();
      await env.SPIKE_KV.put(KV_UNIVERSE, JSON.stringify({ built_at, entries: job.universe }));
      await env.SPIKE_KV.put(KV_BASELINE, JSON.stringify({ built_at, avg_daily_volume: job.baseline }));
      console.log(`published universe ${job.universe!.length}, baseline ${Object.keys(job.baseline!).length}`);
      // Daily heartbeat: confirms Telegram works and that the detector is alive.
      await telegram(env, `Spike detector: universe rebuilt — ${job.universe!.length} pairs, ` +
                          `baselines for ${Object.keys(job.baseline!).length}. Scanning.`);
      return st.setJob({ phase: "done", startedAt: job.startedAt });
    }
  }
}
