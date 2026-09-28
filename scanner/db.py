"""Supabase persistence. Falls back to a local JSON store when SUPABASE_URL is unset,
so the scanner and tests run without any cloud account."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from .config import env, ROOT

_LOCAL = ROOT / "data" / "local_store.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self):
        url, key = env("SUPABASE_URL"), env("SUPABASE_SERVICE_ROLE_KEY")
        self.sb = None
        if url and key:
            from supabase import create_client
            self.sb = create_client(url, key)
        else:
            _LOCAL.parent.mkdir(exist_ok=True)
            self._local = json.loads(_LOCAL.read_text()) if _LOCAL.exists() else {}
            for t in ("in_play", "alerts", "journal", "catalysts", "footprints", "scoreboard_daily"):
                self._local.setdefault(t, [])

    # ----------------------------------------------------------- generic
    def _save_local(self):
        _LOCAL.write_text(json.dumps(self._local, indent=2, default=str))

    def insert(self, table: str, row: dict) -> dict:
        row = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in row.items()}
        if self.sb:
            res = self.sb.table(table).insert(row).execute()
            return res.data[0] if res.data else row
        row.setdefault("id", f"local-{len(self._local[table]) + 1}")
        row.setdefault("created_at", _now())
        self._local[table].append(row)
        self._save_local()
        return row

    def upsert(self, table: str, row: dict, on_conflict: str) -> dict:
        row = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in row.items()}
        if self.sb:
            res = self.sb.table(table).upsert(row, on_conflict=on_conflict).execute()
            return res.data[0] if res.data else row
        keys = [k.strip() for k in on_conflict.split(",")]
        for i, r in enumerate(self._local[table]):
            if all(str(r.get(k)) == str(row.get(k)) for k in keys):
                self._local[table][i] = {**r, **row}
                self._save_local()
                return self._local[table][i]
        return self.insert(table, row)

    def update(self, table: str, id_: str, patch: dict) -> None:
        patch = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in patch.items()}
        if self.sb:
            self.sb.table(table).update(patch).eq("id", id_).execute()
            return
        for r in self._local[table]:
            if r.get("id") == id_:
                r.update(patch)
        self._save_local()

    def select(self, table: str, **eq) -> list[dict]:
        if self.sb:
            q = self.sb.table(table).select("*")
            for k, v in eq.items():
                q = q.eq(k, v)
            return q.execute().data
        rows = self._local[table]
        return [r for r in rows if all(str(r.get(k)) == str(v) for k, v in eq.items())]

    # ----------------------------------------------------------- domain helpers
    def watching(self) -> list[dict]:
        return self.select("in_play", status="watching")

    def open_alerts(self) -> list[dict]:
        rows = self.select("alerts")
        return [r for r in rows if r.get("outcome") in (None, "open")]
