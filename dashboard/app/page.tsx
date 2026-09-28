import { supabase, type Alert } from "@/lib/supabase";

export const revalidate = 60;

const pct = (v: number | null | undefined, d = 1) => v == null ? "–" : `${v > 0 ? "+" : ""}${v.toFixed(d)}%`;
const num = (v: number) => v >= 100 ? v.toFixed(2) : v.toFixed(4);
const cls = (v: number | null | undefined) => v == null ? "muted" : v > 0 ? "up" : "down";

export default async function AlertsPage() {
  const { data } = await supabase.from("alerts").select("*").order("fired_at", { ascending: false }).limit(100);
  const alerts = (data ?? []) as Alert[];
  const open = alerts.filter(a => !a.outcome || a.outcome === "open");
  return (
    <>
      <h1>Alerts <span className="muted">({open.length} open)</span></h1>
      <div className="wrap">
        <table>
          <thead><tr>
            <th>Fired</th><th>Symbol</th><th>Entry</th><th>Stop</th><th>T1</th><th>T2</th><th>R:R</th><th>Size</th>
            <th>Outcome</th><th>Rule ret</th><th>R</th><th>Hold 7d</th><th>MFE/MAE 7d</th><th>Notes</th>
          </tr></thead>
          <tbody>
            {alerts.map(a => (
              <tr key={a.id}>
                <td>{new Date(a.fired_at).toLocaleString()}</td>
                <td><strong>{a.symbol}</strong></td>
                <td>{num(a.entry)}</td><td>{num(a.stop)}</td><td>{num(a.target1)}</td><td>{num(a.target2)}</td>
                <td>{a.reward_risk.toFixed(1)}</td><td>${a.position_usd.toFixed(0)}</td>
                <td className={a.outcome === "stop" ? "down" : a.outcome && a.outcome !== "open" ? "up" : "muted"}>{a.outcome ?? "open"}</td>
                <td className={cls(a.rule_return)}>{pct(a.rule_return)}</td>
                <td className={cls(a.r_multiple)}>{a.r_multiple?.toFixed(2) ?? "–"}</td>
                <td className={cls(a.hold_7d_return)}>{pct(a.hold_7d_return)}</td>
                <td><span className="up">{pct(a.mfe_7d)}</span> / <span className="down">{pct(a.mae_7d)}</span></td>
                <td className="muted">{a.notes}</td>
              </tr>
            ))}
            {alerts.length === 0 && <tr><td colSpan={14} className="muted">No alerts yet. The scanner writes here when a setup fires.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
