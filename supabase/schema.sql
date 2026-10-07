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
  exchange        text,                        -- price source; null = configured exchange (Kraken)
  late            boolean not null default false,  -- first seen too late for a breakout entry; pullback only
  source          text,                        -- null = Stage A breakout; 'listing' = exchange-listing watcher
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
  exchange        text,                        -- price source; null = configured exchange (Kraken)
  stale           boolean not null default false,  -- fired at a price already gone: record only, not a position, not scored
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
  -- Exchange listings (event_type 'listing', source upbit|bithumb|binance|coinbase); null for calendar events
  source_id          text,
  announced_at       timestamptz,
  detected_at        timestamptz,
  coinbase_tradeable boolean,
  trading_open       boolean,                  -- on the announcing exchange, when detected
  notified           boolean,
  price_source       text,                     -- coinbase | kraken (USD prices below)
  price_pre          double precision,         -- last 1m close before the announcement
  price_detect       double precision,         -- when the watcher saw it
  price_1h           double precision,
  price_24h          double precision,
  created_at      timestamptz not null default now(),
  unique (symbol, event_date, event_type, source)
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
-- (First version used outcome = 'skipped_concurrent'; kept in the check for old rows.)
alter table alerts drop constraint if exists alerts_outcome_check;
alter table alerts add constraint alerts_outcome_check check (outcome in ('open','stop','t1','t2','expired','skipped_concurrent'));
-- skipped_concurrent is no longer written: skipped setups are graded like the rest and
-- marked taken = false instead, so the scoreboard can show tool vs trader.
alter table alerts add column if not exists taken boolean not null default true;
alter table scoreboard_daily add column if not exists trader_n_graded int;
alter table scoreboard_daily add column if not exists trader_win_rate double precision;
alter table scoreboard_daily add column if not exists trader_avg_r double precision;

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
-- Journal writes from the dashboard: allow anon insert/update/delete on journal only.
-- (Tighten to authenticated users once you add Supabase Auth to the dashboard.)
create policy "anon write journal" on journal for insert to anon with check (true);
create policy "anon update journal" on journal for update to anon using (true);
create policy "anon delete journal" on journal for delete to anon using (true);

-- ---------------------------------------------------------------- spike detector (spike-worker/)
-- One row per spike alert. Detection and measurement only: size/stop/take_profit are suggestions.
create table if not exists spike_alerts (
  id               uuid primary key default gen_random_uuid(),
  symbol           text not null,                 -- base symbol, e.g. QNT
  exchange         text not null check (exchange in ('kraken','coinbase')),
  pair_id          text not null,                 -- Kraken ticker key or Coinbase product_id (for grading)
  fired_at         timestamptz not null,
  price_at_alert   double precision not null,
  price_30m_ago    double precision,
  high_30m         double precision,
  move_30m         double precision,              -- %
  vol_multiple     double precision,              -- 30-min volume / (30-day avg daily volume / 48)
  liquidity_label  text check (liquidity_label in ('thin','ok','liquid')),
  vol_24h          double precision,              -- 24h quote volume, USD
  has_news         boolean,                       -- null = CryptoPanic not configured / failed
  news_headline    text,
  reddit_ratio     double precision,
  prior_spikes_90d int,
  size_usd         double precision,
  stop             double precision,
  take_profit      double precision,
  -- Filled by the grader (every 10 min until 240 min have elapsed). Returns in %.
  ret_15 double precision, ret_30 double precision, ret_60 double precision, ret_240 double precision,
  mfe_240 double precision, mae_240 double precision,
  hit_tp_first     boolean,
  hit_stop_first   boolean,
  net_60           double precision,              -- ret_60 − 1.5 (costs)
  graded_complete  boolean not null default false,
  graded_at        timestamptz
);
create index if not exists spike_alerts_fired_idx on spike_alerts (fired_at desc);
create index if not exists spike_alerts_symbol_idx on spike_alerts (symbol, fired_at desc);
create index if not exists spike_alerts_ungraded_idx on spike_alerts (fired_at) where not graded_complete;

-- Daily scoreboard, one row per segment: overall, liquidity:{thin,ok,liquid}, news:{yes,no,unknown}.
create table if not exists spike_scoreboard (
  day              date not null,
  segment          text not null,
  n                int,
  mean_ret_15 double precision, median_ret_15 double precision,
  mean_ret_30 double precision, median_ret_30 double precision,
  mean_ret_60 double precision, median_ret_60 double precision,
  mean_ret_240 double precision, median_ret_240 double precision,
  mean_net_60 double precision, median_net_60 double precision,
  pct_tp_first     double precision,
  pct_stop_first   double precision,
  primary key (day, segment)
);

alter table spike_alerts enable row level security;
alter table spike_scoreboard enable row level security;
create policy "anon read spike_alerts" on spike_alerts for select to anon using (true);
create policy "anon read spike_scoreboard" on spike_scoreboard for select to anon using (true);

-- Shadow mode + per-alert cost (also in supabase/migrations/2026-09-29_spike_shadow_mode.sql)
alter table spike_alerts add column if not exists shadow boolean not null default false;  -- true = micro coin (< $1M/day): graded, sent marked MICRO (never sent before 2026-09-29)
alter table spike_alerts add column if not exists spread_pct double precision;             -- (ask − bid) / mid at alert, %
alter table spike_alerts add column if not exists cost_pct double precision;               -- spread + 2 × taker fee, %
alter table spike_alerts add column if not exists net_60_real double precision;            -- ret_60 − cost_pct
alter table spike_alerts drop constraint if exists spike_alerts_liquidity_label_check;
alter table spike_alerts add constraint spike_alerts_liquidity_label_check
  check (liquidity_label in ('micro','thin','ok','liquid'));
alter table spike_scoreboard add column if not exists mean_net_60_real double precision;
alter table spike_scoreboard add column if not exists median_net_60_real double precision;

-- Early-warning alerts (also in supabase/migrations/2026-09-30_spike_early_warning.sql)
alter table spike_alerts add column if not exists kind text not null default 'spike';  -- 'early': price_30m_ago / high_30m / move_30m hold the 15-minute window's values
alter table spike_alerts drop constraint if exists spike_alerts_kind_check;
alter table spike_alerts add constraint spike_alerts_kind_check check (kind in ('spike','early'));

-- Listing-watcher source health (scanner/listings.py): consecutive failed runs per source,
-- so "source down" / "recovered" are each sent once. Written with the service role only.
create table if not exists source_health (
  source      text primary key,              -- upbit | bithumb | binance | coinbase
  failures    integer not null default 0,    -- consecutive failed runs
  down        boolean not null default false,
  last_error  text,
  updated_at  timestamptz not null default now()
);
alter table source_health enable row level security;
