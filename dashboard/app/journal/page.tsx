"use client";
import { useEffect, useState } from "react";
import { supabase, type Journal } from "@/lib/supabase";

export default function JournalPage() {
  const [rows, setRows] = useState<Journal[]>([]);
  const [f, setF] = useState({ symbol: "", entry: "", exit: "", size_usd: "", followed_rules: "true", note: "" });

  const load = async () => {
    const { data } = await supabase.from("journal").select("*").order("opened_at", { ascending: false }).limit(200);
    setRows((data ?? []) as Journal[]);
  };
  useEffect(() => { load(); }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const entry = parseFloat(f.entry), exit = f.exit ? parseFloat(f.exit) : null, size = parseFloat(f.size_usd);
    const pnl_pct = exit != null ? (exit / entry - 1) * 100 : null;
    await supabase.from("journal").insert({
      symbol: f.symbol.toUpperCase(), entry, exit, size_usd: size,
      pnl_pct, pnl_usd: pnl_pct != null ? size * pnl_pct / 100 : null,
      closed_at: exit != null ? new Date().toISOString() : null,
      followed_rules: f.followed_rules === "true", note: f.note,
    });
    setF({ symbol: "", entry: "", exit: "", size_usd: "", followed_rules: "true", note: "" });
    load();
  };

  const closed = rows.filter(r => r.pnl_usd != null);
  const total = closed.reduce((s, r) => s + (r.pnl_usd ?? 0), 0);
  const wins = closed.filter(r => (r.pnl_usd ?? 0) > 0).length;

  return (
    <>
      <h1>Journal</h1>
      <div className="tiles">
        <div className="tile"><div className="k">Closed trades</div><div className="v">{closed.length}</div></div>
        <div className="tile"><div className="k">Win rate</div><div className="v">{closed.length ? `${Math.round(wins / closed.length * 100)}%` : "–"}</div></div>
        <div className="tile"><div className="k">Net P&L</div><div className={`v ${total >= 0 ? "up" : "down"}`}>${total.toFixed(0)}</div></div>
        <div className="tile"><div className="k">Followed rules</div><div className="v">{closed.length ? `${Math.round(closed.filter(r => r.followed_rules).length / closed.length * 100)}%` : "–"}</div></div>
      </div>
      <form onSubmit={submit}>
        <input placeholder="Symbol" value={f.symbol} onChange={e => setF({ ...f, symbol: e.target.value })} required />
        <input placeholder="Entry" type="number" step="any" value={f.entry} onChange={e => setF({ ...f, entry: e.target.value })} required />
        <input placeholder="Exit (blank if open)" type="number" step="any" value={f.exit} onChange={e => setF({ ...f, exit: e.target.value })} />
        <input placeholder="Size USD" type="number" step="any" value={f.size_usd} onChange={e => setF({ ...f, size_usd: e.target.value })} required />
        <select value={f.followed_rules} onChange={e => setF({ ...f, followed_rules: e.target.value })}>
          <option value="true">Followed rules</option><option value="false">Broke rules</option>
        </select>
        <input placeholder="Why did you take it?" value={f.note} onChange={e => setF({ ...f, note: e.target.value })} />
        <button type="submit">Log trade</button>
      </form>
      <div className="wrap">
        <table>
          <thead><tr><th>Opened</th><th>Symbol</th><th>Entry</th><th>Exit</th><th>Size</th><th>P&L</th><th>%</th><th>Rules</th><th>Note</th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id}>
                <td>{new Date(r.opened_at).toLocaleDateString()}</td><td><strong>{r.symbol}</strong></td>
                <td>{r.entry ?? "–"}</td><td>{r.exit ?? <span className="muted">open</span>}</td><td>${r.size_usd?.toFixed(0)}</td>
                <td className={(r.pnl_usd ?? 0) >= 0 ? "up" : "down"}>{r.pnl_usd == null ? "–" : `$${r.pnl_usd.toFixed(0)}`}</td>
                <td className={(r.pnl_pct ?? 0) >= 0 ? "up" : "down"}>{r.pnl_pct == null ? "–" : `${r.pnl_pct.toFixed(1)}%`}</td>
                <td>{r.followed_rules == null ? "–" : r.followed_rules ? "✓" : "✗"}</td><td className="muted">{r.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
