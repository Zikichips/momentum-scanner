-- Listing-watcher source health: consecutive failed runs per source, so "source down" and
-- "recovered" Telegram lines are each sent once. Service role only (RLS on, no policies).
-- Safe to run more than once.
create table if not exists source_health (
  source      text primary key,
  failures    integer not null default 0,
  down        boolean not null default false,
  last_error  text,
  updated_at  timestamptz not null default now()
);
alter table source_health enable row level security;
