-- Journal: let the dashboard delete its own rows (Delete button on the Journal page).
-- Same trust level as the existing anon insert/update policies; tighten all three when Supabase Auth is added.
-- Safe to run more than once.
drop policy if exists "anon delete journal" on journal;
create policy "anon delete journal" on journal for delete to anon using (true);
