import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export type Alert = {
  id: string; symbol: string; asset_class: string; fired_at: string;
  entry: number; stop: number; target1: number; target2: number; reward_risk: number;
  position_usd: number; retrace_pct: number; notes: string | null;
  entry_type: "pullback" | "breakout" | null;
  taken: boolean | null;
  outcome: "open" | "stop" | "t1" | "t2" | "expired" | "skipped_concurrent" | null; outcome_at: string | null;
  mfe_7d: number | null; mae_7d: number | null; hold_7d_return: number | null;
  rule_return: number | null; r_multiple: number | null;
};
export type Scoreboard = {
  day: string; alerts_total: number; alerts_graded: number; wins: number; losses: number;
  win_rate: number | null; avg_r: number | null; expectancy_r: number | null; vs_hold_7d: number | null;
  pullback_n_graded: number | null; pullback_win_rate: number | null; pullback_avg_r: number | null;
  breakout_n_graded: number | null; breakout_win_rate: number | null; breakout_avg_r: number | null;
  trader_n_graded: number | null; trader_win_rate: number | null; trader_avg_r: number | null;
};
export type Journal = {
  id: string; alert_id: string | null; symbol: string; opened_at: string; closed_at: string | null;
  entry: number | null; exit: number | null; size_usd: number | null; pnl_usd: number | null;
  pnl_pct: number | null; followed_rules: boolean | null; note: string | null;
};

export type SpikeAlert = {
  id: string; symbol: string; exchange: "kraken" | "coinbase"; fired_at: string; price_at_alert: number;
  move_30m: number | null; vol_multiple: number | null; liquidity_label: "thin" | "ok" | "liquid" | null;
  vol_24h: number | null; has_news: boolean | null; news_headline: string | null;
  ret_15: number | null; ret_30: number | null; ret_60: number | null; ret_240: number | null;
  mfe_240: number | null; mae_240: number | null; hit_tp_first: boolean | null; hit_stop_first: boolean | null;
  net_60: number | null; graded_complete: boolean;
};
export type SpikeScoreboardRow = {
  day: string; segment: string; n: number;
  mean_ret_15: number | null; median_ret_15: number | null; mean_ret_30: number | null; median_ret_30: number | null;
  mean_ret_60: number | null; median_ret_60: number | null; mean_ret_240: number | null; median_ret_240: number | null;
  mean_net_60: number | null; median_net_60: number | null; pct_tp_first: number | null; pct_stop_first: number | null;
};
