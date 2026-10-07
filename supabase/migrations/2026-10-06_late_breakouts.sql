-- Late breakouts and stale alerts.
-- in_play.late: breakout first seen too late (or price ran away) for a breakout entry; Stage B still watches it.
-- alerts.stale: alert fired at a price that was already gone. Kept for the record; not a position, not scored.
-- Safe to run more than once.
alter table in_play add column if not exists late  boolean not null default false;
alter table alerts  add column if not exists stale boolean not null default false;
