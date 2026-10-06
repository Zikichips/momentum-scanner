-- Coinbase movers in the Stage A universe: rows record where their prices come from.
-- null = the configured exchange (Kraken); 'coinbase' = a Coinbase mover outside the Kraken top-N.
-- Safe to run more than once.
alter table in_play add column if not exists exchange text;
alter table alerts  add column if not exists exchange text;
