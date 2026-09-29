// Pure functions: spike condition, suggested levels, message, grading, scoreboard.
// No I/O, so they are unit-tested directly (test/rules.test.ts).
import { RULES } from "./config";

export interface Candle { t: number; open: number; high: number; low: number; close: number; volume: number } // t = start, ms

export type Exchange = "kraken" | "coinbase";
export type Liquidity = "thin" | "ok" | "liquid";

export interface SpikeCheck {
  ok: boolean;
  move: number;          // fraction
  volMultiple: number;
  priceAgo: number;
  high: number;
  reasons: string[];     // failed conditions, for logs
}

/** The three spike conditions on 1-minute candles covering the last 30 minutes.
 *  avgDailyVolume is in base units, like candle volume. */
export function evaluateSpike(candles: Candle[], priceNow: number, avgDailyVolume: number, now: number): SpikeCheck {
  const from = now - RULES.windowMin * 60_000;
  const w = candles.filter(c => c.t >= from && c.t <= now).sort((a, b) => a.t - b.t);
  const fail = (r: string): SpikeCheck => ({ ok: false, move: 0, volMultiple: 0, priceAgo: 0, high: 0, reasons: [r] });
  if (w.length === 0) return fail("no candles");
  if (!(avgDailyVolume > 0)) return fail("no baseline");
  // A window that starts late (thin pair, no trades at the start) would understate the move's base.
  if (w[0].t - from > 5 * 60_000) return fail("window starts late");

  const priceAgo = w[0].open;
  const high = Math.max(priceNow, ...w.map(c => c.high));
  const vol = w.reduce((s, c) => s + c.volume, 0);
  const move = priceNow / priceAgo - 1;
  const volMultiple = vol / (avgDailyVolume / 48);
  const reasons: string[] = [];
  if (!(move >= RULES.minMove)) reasons.push(`move ${(move * 100).toFixed(1)}%`);
  if (!(volMultiple >= RULES.volumeMultiple)) reasons.push(`vol ${volMultiple.toFixed(1)}x`);
  if (!(priceNow >= RULES.nearHigh * high)) reasons.push(`off high ${((priceNow / high - 1) * 100).toFixed(1)}%`);
  return { ok: reasons.length === 0, move, volMultiple, priceAgo, high, reasons };
}

export function liquidityLabel(quoteVolume24h: number): Liquidity {
  if (quoteVolume24h < RULES.liquidity.thin) return "thin";
  if (quoteVolume24h > RULES.liquidity.liquid) return "liquid";
  return "ok";
}

/** Same as scanner/strategy.py position_size(): dollars so a stop-out costs riskPct of capital, capped. */
export function positionSize(entry: number, stop: number, capital: number, riskPct: number, maxPositionPct: number): number {
  const perUnitRisk = (entry - stop) / entry;
  if (!(perUnitRisk > 0)) return 0;
  const size = (capital * riskPct / 100) / perUnitRisk;
  return Math.round(Math.min(size, capital * maxPositionPct / 100) * 100) / 100;
}

export interface Levels { stop: number; takeProfit: number; stopPct: number; tpPct: number }

export function levels(priceNow: number, priceAgo: number): Levels {
  const stop = Math.max(priceAgo, priceNow * RULES.stopFloor);
  const takeProfit = priceNow + RULES.tpMultiple * (priceNow - stop);
  return { stop, takeProfit, stopPct: (1 - stop / priceNow) * 100, tpPct: (takeProfit / priceNow - 1) * 100 };
}

// ------------------------------------------------------------------ message
export function fmtPrice(p: number): string {
  if (!isFinite(p)) return "–";
  const s = Number(p.toPrecision(4));
  return Math.abs(s) >= 1e4 ? Math.round(s).toString() : s.toString();
}

export function fmtUsd(v: number): string {
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}k`;
  return v.toFixed(0);
}

const signed = (v: number | null | undefined, d = 1) =>
  v == null || !isFinite(v) ? "n/a" : `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(d)}`;

export interface AlertView {
  symbol: string; exchange: Exchange; move30: number; volMultiple: number; price: number; high: number;
  chg24h: number | null; chg7d: number | null; liquidity: Liquidity; vol24h: number;
  headline: string | null;
  reddit: { m24: number; avg7d: number } | null;
  prior: { n: number; avgRet60: number | null };
  size: number; lv: Levels;
}

export function formatAlert(a: AlertView): string {
  const ex = a.exchange === "kraken" ? "Kraken" : "Coinbase";
  const reddit = a.reddit
    ? `${a.reddit.m24} vs baseline ${a.reddit.avg7d.toFixed(1)} (${a.reddit.avg7d > 0 ? (a.reddit.m24 / a.reddit.avg7d).toFixed(1) : "n/a"}×)`
    : "n/a";
  return [
    `SPIKE — ${a.symbol}   ${ex}`,
    `+${(a.move30 * 100).toFixed(1)}% in 30 min · vol ${a.volMultiple.toFixed(1)}× · now ${fmtPrice(a.price)} (30m high ${fmtPrice(a.high)})`,
    `24h ${signed(a.chg24h)}% · 7d ${signed(a.chg7d)}% · liquidity ${a.liquidity} ($${fmtUsd(a.vol24h)}/24h)`,
    `News 6h: ${a.headline ?? "none"}`,
    `Reddit: ${reddit}`,
    `Prior spikes 90d: ${a.prior.n} · avg +60min ${a.prior.avgRet60 == null ? "n/a" : signed(a.prior.avgRet60) + "%"}`,
    `Size $${a.size.toFixed(0)} · stop ${fmtPrice(a.lv.stop)} (−${a.lv.stopPct.toFixed(1)}%) · TP ${fmtPrice(a.lv.takeProfit)} (+${a.lv.tpPct.toFixed(1)}%)`,
  ].join("\n");
}

// ------------------------------------------------------------------ grading
export interface GradeInput { firedAt: number; price: number; stop: number; takeProfit: number }
export interface GradePatch {
  ret_15?: number; ret_30?: number; ret_60?: number; ret_240?: number;
  mfe_240?: number; mae_240?: number;
  hit_tp_first?: boolean; hit_stop_first?: boolean;
  net_60?: number; graded_complete: boolean;
}

const pct = (x: number, base: number) => Math.round((x / base - 1) * 100 * 1000) / 1000;

/** Measure the path after an alert. candles: 1-min bars after fired_at. Horizons that haven't
 *  elapsed yet are left out; the row is complete once 240 minutes have passed. */
export function gradePath(a: GradeInput, candles: Candle[], now: number): GradePatch {
  const horizonEnd = a.firedAt + 240 * 60_000;
  const bars = candles.filter(c => c.t >= a.firedAt && c.t + 60_000 <= Math.min(now, horizonEnd) + 1).sort((x, y) => x.t - y.t);
  const complete = now >= horizonEnd;
  const patch: GradePatch = { graded_complete: complete };

  for (const h of RULES.gradeHorizonsMin) {
    const end = a.firedAt + h * 60_000;
    if (now < end) continue;
    const upto = bars.filter(c => c.t + 60_000 <= end + 1);
    if (upto.length) (patch as any)[`ret_${h}`] = pct(upto[upto.length - 1].close, a.price);
  }
  if (patch.ret_60 != null) patch.net_60 = Math.round((patch.ret_60 - RULES.costsPct) * 1000) / 1000;

  if (bars.length) {
    patch.mfe_240 = pct(Math.max(...bars.map(c => c.high)), a.price);
    patch.mae_240 = pct(Math.min(...bars.map(c => c.low)), a.price);
  }
  // Which suggested level was touched first. Both inside one bar: count the stop (conservative).
  let first: "tp" | "stop" | null = null;
  for (const c of bars) {
    if (c.low <= a.stop) { first = "stop"; break; }
    if (c.high >= a.takeProfit) { first = "tp"; break; }
  }
  if (first || complete) {
    patch.hit_tp_first = first === "tp";
    patch.hit_stop_first = first === "stop";
  }
  return patch;
}

// ------------------------------------------------------------------ scoreboard
export interface GradedRow {
  liquidity_label: Liquidity; has_news: boolean | null;
  ret_15: number | null; ret_30: number | null; ret_60: number | null; ret_240: number | null; net_60: number | null;
  hit_tp_first: boolean | null; hit_stop_first: boolean | null;
}

const mean = (xs: number[]) => xs.length ? Math.round(xs.reduce((s, x) => s + x, 0) / xs.length * 1000) / 1000 : null;
const median = (xs: number[]) => {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b), m = Math.floor(s.length / 2);
  return Math.round((s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2) * 1000) / 1000;
};

export function segmentStats(rows: GradedRow[]) {
  const out: Record<string, number | null> = { n: rows.length };
  for (const k of ["ret_15", "ret_30", "ret_60", "ret_240", "net_60"] as const) {
    const xs = rows.map(r => r[k]).filter((x): x is number => x != null);
    out[`mean_${k}`] = mean(xs);
    out[`median_${k}`] = median(xs);
  }
  out.pct_tp_first = rows.length ? Math.round(rows.filter(r => r.hit_tp_first).length / rows.length * 1000) / 10 : null;
  out.pct_stop_first = rows.length ? Math.round(rows.filter(r => r.hit_stop_first).length / rows.length * 1000) / 10 : null;
  return out;
}

export interface ScoreRow { day: string; segment: string; [stat: string]: string | number | null }

/** One row per segment: overall, liquidity:{thin,ok,liquid}, news:{yes,no,unknown}. */
export function scoreboard(day: string, rows: GradedRow[]): ScoreRow[] {
  const segs: [string, GradedRow[]][] = [
    ["overall", rows],
    ...(["thin", "ok", "liquid"] as const).map(l => [`liquidity:${l}`, rows.filter(r => r.liquidity_label === l)] as [string, GradedRow[]]),
    ["news:yes", rows.filter(r => r.has_news === true)],
    ["news:no", rows.filter(r => r.has_news === false)],
    ["news:unknown", rows.filter(r => r.has_news == null)],   // CryptoPanic not configured or failed
  ];
  return segs.map(([segment, rs]) => ({ day, segment, ...segmentStats(rs) }));
}
