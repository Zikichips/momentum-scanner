-- Spike detector: early-warning alerts (+8% in 15 min, coins >= $1M), graded and scored separately.
-- Safe to run more than once. Run this BEFORE deploying the matching Worker version.
alter table spike_alerts add column if not exists kind text not null default 'spike';  -- 'early': price_30m_ago / high_30m / move_30m hold the 15-minute window's values
alter table spike_alerts drop constraint if exists spike_alerts_kind_check;
alter table spike_alerts add constraint spike_alerts_kind_check check (kind in ('spike','early'));
