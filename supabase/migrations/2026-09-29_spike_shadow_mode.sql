-- Spike detector: shadow mode for micro coins (< $1M/day) and per-alert trading cost.
-- Safe to run more than once. Run this BEFORE deploying the matching Worker version.
alter table spike_alerts add column if not exists shadow boolean not null default false;  -- true = graded, never sent
alter table spike_alerts add column if not exists spread_pct double precision;             -- (ask − bid) / mid at alert, %
alter table spike_alerts add column if not exists cost_pct double precision;               -- spread + 2 × taker fee, %
alter table spike_alerts add column if not exists net_60_real double precision;            -- ret_60 − cost_pct
alter table spike_alerts drop constraint if exists spike_alerts_liquidity_label_check;
alter table spike_alerts add constraint spike_alerts_liquidity_label_check
  check (liquidity_label in ('micro','thin','ok','liquid'));
alter table spike_scoreboard add column if not exists mean_net_60_real double precision;
alter table spike_scoreboard add column if not exists median_net_60_real double precision;
