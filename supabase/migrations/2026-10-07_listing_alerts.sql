-- Listing alerts scored as their own group: alerts.source = 'listing' (copied from in_play.source
-- when Stage B fires on a listing). Safe to run more than once.
alter table alerts add column if not exists source text;
alter table scoreboard_daily add column if not exists listing_n_graded int;
alter table scoreboard_daily add column if not exists listing_win_rate double precision;
alter table scoreboard_daily add column if not exists listing_avg_r double precision;
