-- Momentum scanner schema. Run once in the Supabase SQL editor.
-- All prices are floats in USD. Times are UTC.

create extension if not exists "pgcrypto";

-- Assets that have passed Stage A (breakout) and are being watched for a pullback.
create table if not exists in_play (
  id              uuid primary key default gen_random_uuid(),
  symbol          text not null,
  asset_class     text not null check (asset_class in ('crypto','stock')),
  breakout_date   date not null,
  breakout_level  double precision not null,   -- the 20-day high that was broken
  impulse_low     double precision not null,   -- start of the impulse move
  impulse_high    double precision not null,   -- peak so far (updated while in play)
  impulse_volume  double precision not null,   -- avg daily volume during impulse
  status          text not null default 'watching' check (status in ('watching','triggered','expired','failed')),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (symbol, breakout_date)
);

-- Setups that fired (Stage B pullback entries and Stage A breakout entries). One row per alert. Never deleted; graded by the outcome tracker.
create table if not exists alerts (
  id              uuid primary key default gen_random_uuid(),
  in_play_id      uuid references in_play(id) on delete set null,
  symbol          text not null,
  asset_class     text not null,
  fired_at        timestamptz not null default now(),
  entry           double precision not null,
  stop            double precision not null,
  target1         double precision not null,
  target2         double precision not null,
  reward_risk     double precision not null,
  position_usd    double precision not null,
  retrace_pct     double precision not null,   -- 0 for breakout entries
  ema_value       double precision,
  notes           text,
  -- Outcome fields, filled by outcomes.py
  outcome         text check (outcome in ('open','stop','t1','t2','expired','skipped_concurrent')),
  outcome_at      timestamptz,
  mfe_1d double precision, mae_1d double precision,
  mfe_3d double precision, mae_3d double precision,
  mfe_7d double precision, mae_7d double precision,
  mfe_14d double precision, mae_14d double precision,
  hold_7d_return double precision,
  hold_14d_return double precision,
  rule_return     double precision,            -- return if rules were followed (stop / t1 half / t2)
  r_multiple      double precision             -- rule_return in units of initial risk
);
create index if not exists alerts_fired_at_idx on alerts (fired_at desc);
create index if not exists alerts_symbol_idx on alerts (symbol);

-- Your actual trades. You fill these in; the dashboard joins them to alerts.
create table if not exists journal (
  id              uuid primary key default gen_random_uuid(),
  alert_id        uuid references alerts(id) on delete set null,
  symbol          text not null,
  opened_at       timestamptz not null default now(),
  closed_at       timestamptz,
  entry           double precision,
  exit            double precision,
  size_usd        double precision,
  pnl_usd         double precision,
  pnl_pct         double precision,
  followed_rules  boolean,
  note            text
);

-- Module 1: scheduled catalysts.
create table if not exists catalysts (
  id              uuid primary key default gen_random_uuid(),
  symbol          text not null,
  asset_class     text not null,
  event_date      date not null,
  event_type      text not null,               -- earnings | unlock | listing | mainnet | fda | other
  lean            text not null check (lean in ('bullish','bearish','binary')),
  title           text,
  source          text,
  source_url      text,
  created_at      timestamptz not null default now(),
  unique (symbol, event_date, event_type)
);

-- Module 2: unusual-activity flags.
create table if not exists footprints (
  id              uuid primary key default gen_random_uuid(),
  symbol          text not null,
  asset_class     text not null,
  observed_at     timestamptz not null default now(),
  volume_multiple double precision,
  move_pct        double precision,
  oi_change_pct   double precision,
  has_news        boolean,
  news_headline   text,
  score           double precision
);
create index if not exists footprints_observed_idx on footprints (observed_at desc);

-- Daily snapshot of the scoreboard so the dashboard can chart it over time.
create table if not exists scoreboard_daily (
  day             date primary key,
  alerts_total    int,
  alerts_graded   int,
  wins            int,
  losses          int,
  win_rate        double precision,
  avg_r           double precision,
  expectancy_r    double precision,
  vs_hold_7d      double precision              -- avg rule_return - avg hold_7d_return
);

-- Migration: entry types (pullback = wait for Stage B, breakout = buy the Stage A close).
-- Safe to re-run; also applies to databases created before entry types existed.
alter table alerts add column if not exists entry_type text default 'pullback';
alter table alerts drop constraint if exists alerts_entry_type_check;
alter table alerts add constraint alerts_entry_type_check check (entry_type in ('pullback','breakout'));
alter table scoreboard_daily add column if not exists pullback_n_graded int;
alter table scoreboard_daily add column if not exists pullback_win_rate double precision;
alter table scoreboard_daily add column if not exists pullback_avg_r double precision;
alter table scoreboard_daily add column if not exists breakout_n_graded int;
alter table scoreboard_daily add column if not exists breakout_win_rate double precision;
alter table scoreboard_daily add column if not exists breakout_avg_r double precision;

-- Migration: setups not taken because max_concurrent_trades positions were open.
alter table alerts drop constraint if exists alerts_outcome_check;
alter table alerts add constraint alerts_outcome_check check (outcome in ('open','stop','t1','t2','expired','skipped_concurrent'));

-- Row-level security: dashboard uses the anon key and may only read.
alter table in_play enable row level security;
alter table alerts enable row level security;
alter table journal enable row level security;
alter table catalysts enable row level security;
alter table footprints enable row level security;
alter table scoreboard_daily enable row level security;

create policy "anon read in_play" on in_play for select to anon using (true);
create policy "anon read alerts" on alerts for select to anon using (true);
create policy "anon read journal" on journal for select to anon using (true);
create policy "anon read catalysts" on catalysts for select to anon using (true);
create policy "anon read footprints" on footprints for select to anon using (true);
create policy "anon read scoreboard" on scoreboard_daily for select to anon using (true);
-- Journal writes from the dashboard: allow anon insert/update on journal only.
-- (Tighten to authenticated users once you add Supabase Auth to the dashboard.)
create policy "anon write journal" on journal for insert to anon with check (true);
create policy "anon update journal" on journal for update to anon using (true);
