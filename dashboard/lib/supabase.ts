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
  outcome: "open" | "stop" | "t1" | "t2" | "expired" | null; outcome_at: string | null;
  mfe_7d: number | null; mae_7d: number | null; hold_7d_return: number | null;
  rule_return: number | null; r_multiple: number | null;
};
export type Scoreboard = {
  day: string; alerts_total: number; alerts_graded: number; wins: number; losses: number;
  win_rate: number | null; avg_r: number | null; expectancy_r: number | null; vs_hold_7d: number | null;
  pullback_n_graded: number | null; pullback_win_rate: number | null; pullback_avg_r: number | null;
  breakout_n_graded: number | null; breakout_win_rate: number | null; breakout_avg_r: number | null;
};
export type Journal = {
  id: string; alert_id: string | null; symbol: string; opened_at: string; closed_at: string | null;
  entry: number | null; exit: number | null; size_usd: number | null; pnl_usd: number | null;
  pnl_pct: number | null; followed_rules: boolean | null; note: string | null;
};
