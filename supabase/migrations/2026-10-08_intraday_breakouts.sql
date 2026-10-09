-- Intraday Stage A: coins put in play on a 1h breakout (in_play.source = 'intraday', no new
-- column). Stage B pullbacks on them carry alerts.source = 'intraday' and are scored as their
-- own group. Safe to run more than once.
alter table scoreboard_daily add column if not exists intraday_n_graded int;
alter table scoreboard_daily add column if not exists intraday_win_rate double precision;
alter table scoreboard_daily add column if not exists intraday_avg_r double precision;
