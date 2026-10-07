// Spike detector. Detection and measurement only: it alerts and grades, it never trades.
//   * * * * *     scan       — quotes for the universe, rolling window, spike + early-warning checks, alert
//   */10 * * * *  grade      — fill ret_15/30/60/240, MFE/MAE, TP/stop-first for recent alerts
//   0 4 * * *     baseline   — start the universe + 30-day baseline rebuild; write the scoreboard
// The rebuild is split into one bounded step per scan tick (CPU and subrequest limits), and
// publishes the universe and baseline to KV once, when complete.
import { BUDGET, RULES } from "./config";
import type { Env } from "./config";
import {
  COINBASE_PAGE, fetchCandles, fetchCoinbasePage, fetchKrakenPairs, fetchKrakenTickerAll, fetchQuotes, mergeUniverse,
  type Quote, type UniverseEntry,
} from "./exchanges";
import {
  EARLY_RULE, evaluateSpike, formatAlert, formatEarlyAlert, formatMicroAlert, gradePath, levels, liquidityLabel, positionSize, scoreboard, tradeCost, type GradedRow,
} from "./rules";
import { hasSupabase, newsHeadline, priorSpikes, redditMentions, sb, telegram } from "./services";
import { fetchFeeds, FEEDS, findHeadline, type Feeds } from "./news";
import type { Job } from "./state";

export { SpikeState } from "./state";

const KV_UNIVERSE = "universe";
const KV_BASELINE = "baseline";
// Put any value under this key (wrangler kv key put rebuild now ...) to start a universe +
// baseline rebuild on the next scan tick. Scanning continues on the current universe meanwhile.
const KV_REBUILD = "rebuild";

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
    // Read-only news check from Cloudflare's network: /news?base=POND
    const url = new URL(req.url);
    if (url.pathname === "/news") {
      const base = (url.searchParams.get("base") ?? "").toUpperCase();
      const u = await env.SPIKE_KV.get<{ entries: UniverseEntry[] }>(KV_UNIVERSE, "json");
      const name = u?.entries.find(e => e.base === base)?.name;
      const f = await fetchFeeds();
      const now = Date.now();
      return Response.json({
        base, name: name ?? null,
        feeds: FEEDS.map(x => ({ source: x.source, items: f.items.filter(i => i.source === x.source).length })),
        failed: f.failed,
        headline_6h: base ? findHeadline(f.items, base, name, now) : null,
        recent: f.items.filter(i => now - i.published <= 6 * 3600_000).length,
      });
    }
    // Upbit notice relay for the Python listing watcher: Upbit returns 403 to GitHub Actions
    // runners. Fixed upstream (Upbit's "trade" announcements only) and token-gated, so it is
    // not an open proxy: /upbit-notices?page=1 with header x-relay-token: RELAY_TOKEN.
    if (url.pathname === "/upbit-notices") {
      if (!env.RELAY_TOKEN || req.headers.get("x-relay-token") !== env.RELAY_TOKEN) return new Response("forbidden", { status: 403 });
      const page = Math.min(Math.max(parseInt(url.searchParams.get("page") ?? "1", 10) || 1, 1), 5);
      const r = await fetch(`https://api-manager.upbit.com/api/v1/announcements?os=web&page=${page}&per_page=20&category=trade`, {
        headers: { "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36", Accept: "application/json" },
      });
      return new Response(r.body, { status: r.status, headers: { "content-type": r.headers.get("content-type") ?? "application/json" } });
    }
    return new Response("spike-detector: see /status", { status: 404 });
  },
};

// ------------------------------------------------------------------ scan (every minute)
async function scan(env: Env, now: number) {
  const [u, b, rebuild] = await Promise.all([
    env.SPIKE_KV.get<{ entries: UniverseEntry[] }>(KV_UNIVERSE, "json"),
    env.SPIKE_KV.get<{ avg_daily_volume: Record<string, number> }>(KV_BASELINE, "json"),
    env.SPIKE_KV.get(KV_REBUILD),
  ]);
  const st = state(env);
  if (rebuild != null) {
    const job = await st.getJob();
    if (!job || job.phase === "done") await st.setJob({ phase: "kraken_pairs", startedAt: now });
    await env.SPIKE_KV.delete(KV_REBUILD);
    console.log("rebuild requested via KV");
  }
  if (!u || !b) {
    // First run (or KV lost): build the universe before scanning.
    const job = await st.getJob();
    if (!job || job.phase === "done") await st.setJob({ phase: "kraken_pairs", startedAt: now });
    await baselineStep(env, now);
    return;
  }

  const quotes = await fetchQuotes(u.entries);
  const prices = Object.fromEntries(Object.entries(quotes).map(([k, q]) => [k, q.price]));
  const { ago, agoTs, agoEarly, cooldown } = await st.tick(now, prices);
  console.log(`scan ${new Date(now).toISOString()}: ${Object.keys(quotes).length}/${u.entries.length} quotes, ` +
              (agoTs ? `window from ${Math.round((now - agoTs) / 60_000)} min ago` : "no 30-min-old snapshot yet"));

  if (ago || agoEarly) {
    const byBase = new Map(u.entries.map(e => [e.base, e]));
    const cooling = (key: string, ms: number) => cooldown[key] != null && now - cooldown[key] < ms;
    const moveFrom = (snap: Record<string, number> | null, base: string, q: Quote) =>
      snap && snap[base] > 0 ? q.price / snap[base] - 1 : -Infinity;
    const quoted = Object.entries(quotes).filter(([base]) => b.avg_daily_volume[base] > 0);
    const moved = quoted
      .filter(([base, q]) => !cooling(base, RULES.cooldownMs) && moveFrom(ago, base, q) >= RULES.prefilterMove)
      .sort((x, y) => moveFrom(ago, y[0], y[1]) - moveFrom(ago, x[0], x[1]));
    // Coins >= $1M get the candle budget first and send alerts. Micro coins (< $1M) are
    // checked with what's left and recorded as shadow alerts: graded, and sent marked MICRO.
    const liquid = moved.filter(([, q]) => q.qvol24 >= RULES.minQuoteVolume24h).slice(0, BUDGET.maxCandidatesPerScan);
    const micro = moved.filter(([, q]) => q.qvol24 < RULES.minQuoteVolume24h).slice(0, BUDGET.maxMicroCandidatesPerScan);
    // Early warnings (coins >= $1M): the rest of the candle budget goes to +6% in 15 min on the
    // snapshots. Spike candidates are checked for an early alert on the candles already fetched.
    const earlyOk = (base: string) => !cooling(`early:${base}`, RULES.early.cooldownMs);
    const taken = new Set(liquid.map(([base]) => base));
    const early = quoted
      .filter(([base, q]) => q.qvol24 >= RULES.minQuoteVolume24h && !taken.has(base) && earlyOk(base)
                              && !cooling(base, RULES.cooldownMs) && moveFrom(agoEarly, base, q) >= RULES.early.prefilterMove)
      .sort((x, y) => moveFrom(agoEarly, y[0], y[1]) - moveFrom(agoEarly, x[0], x[1]))
      .slice(0, BUDGET.maxCandidatesPerScan - liquid.length);

    // Spike and early alerts share maxAlertsPerScan (subrequest budget).
    let alerts = 0, shadows = 0;
    // News feeds: fetched at most once per scan, and only if a live alert fires.
    let feedsP: Promise<Feeds> | null = null;
    const feeds = () => (feedsP ??= fetchFeeds().then(f => {
      if (f.failed.length) console.log("news feeds failed:", f.failed.join("; "));
      return f;
    }));
    const candidates = [
      ...liquid.map(([base, q]) => ({ base, q, mode: "spike" as const })),
      ...early.map(([base, q]) => ({ base, q, mode: "early" as const })),
      ...micro.map(([base, q]) => ({ base, q, mode: "micro" as const })),
    ];
    for (const { base, q, mode } of candidates) {
      if (mode === "micro" ? shadows >= BUDGET.maxShadowPerScan : alerts >= BUDGET.maxAlertsPerScan) continue;
      const e = byBase.get(base)!;
      const avg = b.avg_daily_volume[base];
      try {
        const windowMin = mode === "early" ? RULES.early.windowMin : RULES.windowMin;
        const candles = await fetchCandles(e, 1, now - (windowMin + 1) * 60_000);
        if (mode !== "early") {
          const chk = evaluateSpike(candles, q.price, avg, now);
          console.log(`candidate ${base} ${e.exchange}${mode === "micro" ? " (micro)" : ""}: ${chk.ok ? "SPIKE" : chk.reasons.join(", ")}`);
          if (chk.ok) {
            if (mode === "micro") { await shadowAlert(env, e, q, chk, now); shadows++; }
            else { await fireAlert(env, e, q, chk, now, feeds); alerts++; }
            await st.markAlert(base, now);
            continue;
          }
          if (mode === "micro" || !earlyOk(base)) continue;
        }
        const chk = evaluateSpike(candles, q.price, avg, now, EARLY_RULE);
        console.log(`candidate ${base} ${e.exchange} (early): ${chk.ok ? "EARLY" : chk.reasons.join(", ")}`);
        if (!chk.ok) continue;
        await earlyAlert(env, e, q, chk, now);
        alerts++;
        await st.markAlert(`early:${base}`, now);
      } catch (err) {
        console.log(`candidate ${base}: ${err}`);
      }
    }
  }

  await baselineStep(env, now);   // no-op unless the daily rebuild is running
}

/** Spike / early / micro alerts go to Telegram unless TELEGRAM_ALERTS is "off" (they are still
 *  stored and graded). The daily heartbeat calls telegram() directly and is never muted. */
async function alertTelegram(env: Env, text: string): Promise<void> {
  if (env.TELEGRAM_ALERTS === "off") { console.log("[telegram alerts muted]"); return; }
  await telegram(env, text);
}

/** Micro coin (< $1M/day) spike: stored and graded like an alert, and sent to Telegram marked
 *  MICRO, but with no enrichment calls. Measures whether thin-coin spikes pay after real costs. */
async function shadowAlert(env: Env, e: UniverseEntry, q: Quote, chk: ReturnType<typeof evaluateSpike>, now: number) {
  const lv = levels(q.price, chk.priceAgo);
  const { spreadPct, costPct } = tradeCost(q.bid, q.ask, e.exchange);
  const row = {
    symbol: e.base, exchange: e.exchange, pair_id: e.id, fired_at: new Date(now).toISOString(), shadow: true,
    price_at_alert: q.price, price_30m_ago: chk.priceAgo, high_30m: chk.high,
    move_30m: Math.round(chk.move * 100_000) / 1000, vol_multiple: Math.round(chk.volMultiple * 100) / 100,
    liquidity_label: "micro", vol_24h: Math.round(q.qvol24), spread_pct: spreadPct, cost_pct: costPct,
    size_usd: positionSize(q.price, lv.stop, +env.CAPITAL_USD, +env.RISK_PCT, +env.MAX_POSITION_PCT),
    stop: lv.stop, take_profit: lv.takeProfit,
  };
  if (hasSupabase(env)) {
    await sb(env, "spike_alerts", { method: "POST", body: JSON.stringify(row), headers: { Prefer: "return=minimal" } })
      .catch(err => console.log("store shadow alert failed:", String(err)));
  }
  console.log(`shadow alert ${e.base} ${e.exchange}: +${row.move_30m}% vol ${row.vol_multiple}x, spread ${spreadPct}%`);
  await alertTelegram(env, formatMicroAlert({
    symbol: e.base, exchange: e.exchange, move30: chk.move, volMultiple: chk.volMultiple, price: q.price, high: chk.high,
    vol24h: q.qvol24, costPct, size: row.size_usd, lv,
  }));
}

/** Early warning (+8% in 15 min, coins >= $1M): stored with kind = 'early' and graded like an
 *  alert, sent marked EARLY, no enrichment calls. price_30m_ago / high_30m / move_30m hold the
 *  15-minute window's values. Measures whether alerting earlier pays after costs. */
async function earlyAlert(env: Env, e: UniverseEntry, q: Quote, chk: ReturnType<typeof evaluateSpike>, now: number) {
  const lv = levels(q.price, chk.priceAgo);
  const { spreadPct, costPct } = tradeCost(q.bid, q.ask, e.exchange);
  const liquidity = liquidityLabel(q.qvol24);
  const row = {
    symbol: e.base, exchange: e.exchange, pair_id: e.id, fired_at: new Date(now).toISOString(), kind: "early", shadow: false,
    price_at_alert: q.price, price_30m_ago: chk.priceAgo, high_30m: chk.high,
    move_30m: Math.round(chk.move * 100_000) / 1000, vol_multiple: Math.round(chk.volMultiple * 100) / 100,
    liquidity_label: liquidity, vol_24h: Math.round(q.qvol24), spread_pct: spreadPct, cost_pct: costPct,
    size_usd: positionSize(q.price, lv.stop, +env.CAPITAL_USD, +env.RISK_PCT, +env.MAX_POSITION_PCT),
    stop: lv.stop, take_profit: lv.takeProfit,
  };
  if (hasSupabase(env)) {
    await sb(env, "spike_alerts", { method: "POST", body: JSON.stringify(row), headers: { Prefer: "return=minimal" } })
      .catch(err => console.log("store early alert failed:", String(err)));
  }
  console.log(`early alert ${e.base} ${e.exchange}: +${row.move_30m}% in 15 min, vol ${row.vol_multiple}x`);
  await alertTelegram(env, formatEarlyAlert({
    symbol: e.base, exchange: e.exchange, move15: chk.move, volMultiple: chk.volMultiple, price: q.price, high: chk.high,
    liquidity, vol24h: q.qvol24, costPct, size: row.size_usd, lv,
  }));
}

async function fireAlert(env: Env, e: UniverseEntry, q: Quote, chk: ReturnType<typeof evaluateSpike>, now: number,
                         feeds: () => Promise<Feeds>) {
  const lv = levels(q.price, chk.priceAgo);
  const size = positionSize(q.price, lv.stop, +env.CAPITAL_USD, +env.RISK_PCT, +env.MAX_POSITION_PCT);
  const [hourly, news, reddit, prior] = await Promise.all([
    fetchCandles(e, 60, now - (7 * 24 + 2) * 3600_000).catch(() => []),
    newsHeadline(env, e.base, e.name, now, feeds),
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
    shadow: false, ...(({ spreadPct, costPct }) => ({ spread_pct: spreadPct, cost_pct: costPct }))(tradeCost(q.bid, q.ask, e.exchange)),
  };
  if (hasSupabase(env)) {
    await sb(env, "spike_alerts", { method: "POST", body: JSON.stringify(row), headers: { Prefer: "return=minimal" } })
      .catch(err => console.log("store alert failed:", String(err)));
  } else {
    console.log("[supabase disabled] alert row", JSON.stringify(row));
  }
  await alertTelegram(env, text);
}

// ------------------------------------------------------------------ grade (every 10 minutes)
async function grade(env: Env, now: number) {
  if (!hasSupabase(env)) return console.log("[supabase disabled] nothing to grade");
  const ready = new Date(now - 15 * 60_000).toISOString();
  const rows: any[] = await sb(env,
    `spike_alerts?graded_complete=eq.false&fired_at=lt.${ready}&order=fired_at.asc&limit=${BUDGET.maxGradesPerRun}` +
    `&select=id,exchange,pair_id,fired_at,price_at_alert,stop,take_profit,cost_pct`);
  for (const r of rows) {
    try {
      const firedAt = Date.parse(r.fired_at);
      const candles = await fetchCandles({ exchange: r.exchange, id: r.pair_id }, 1, firedAt);
      const patch = gradePath({ firedAt, price: r.price_at_alert, stop: r.stop, takeProfit: r.take_profit, costPct: r.cost_pct },
                              candles, now);
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
      "spike_alerts?graded_complete=eq.true&select=kind,liquidity_label,has_news,shadow,ret_15,ret_30,ret_60,ret_240,net_60,net_60_real,hit_tp_first,hit_stop_first");
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
