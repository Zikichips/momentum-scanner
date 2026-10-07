-- Exchange-listing watcher (scanner/listings.py). Safe to run more than once.
alter table in_play add column if not exists source text;   -- null = Stage A breakout; 'listing'

alter table catalysts add column if not exists source_id          text;
alter table catalysts add column if not exists announced_at       timestamptz;
alter table catalysts add column if not exists detected_at        timestamptz;
alter table catalysts add column if not exists coinbase_tradeable boolean;
alter table catalysts add column if not exists trading_open       boolean;
alter table catalysts add column if not exists notified           boolean;
alter table catalysts add column if not exists price_source       text;
alter table catalysts add column if not exists price_pre          double precision;
alter table catalysts add column if not exists price_detect       double precision;
alter table catalysts add column if not exists price_1h           double precision;
alter table catalysts add column if not exists price_24h          double precision;

-- One row per exchange: Upbit and Bithumb listing the same coin on the same day are two rows.
alter table catalysts drop constraint if exists catalysts_symbol_event_date_event_type_key;
alter table catalysts drop constraint if exists catalysts_symbol_event_date_event_type_source_key;
alter table catalysts add constraint catalysts_symbol_event_date_event_type_source_key unique (symbol, event_date, event_type, source);
