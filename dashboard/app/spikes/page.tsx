import { supabase, type SpikeAlert, type SpikeScoreboardRow } from "@/lib/supabase";

export const revalidate = 60;

const pct = (v: number | null | undefined, d = 1) => v == null ? "–" : `${v > 0 ? "+" : ""}${v.toFixed(d)}%`;
const cls = (v: number | null | undefined) => v == null ? "muted" : v > 0 ? "up" : "down";
const SEGMENTS = ["overall", "liquidity:thin", "liquidity:ok", "liquidity:liquid", "news:yes", "news:no", "news:unknown", "liquidity:micro"];

export default async function SpikesPage() {
  const [{ data: sb }, { data: al }] = await Promise.all([
    supabase.from("spike_scoreboard").select("*").order("day", { ascending: false }).limit(SEGMENTS.length),
    supabase.from("spike_alerts").select("*").order("fired_at", { ascending: false }).limit(100),
  ]);
  const rows = (sb ?? []) as SpikeScoreboardRow[];
  const day = rows[0]?.day;
  const bySeg = new Map(rows.filter(r => r.day === day).map(r => [r.segment, r]));
  const alerts = (al ?? []) as SpikeAlert[];

  return (
    <>
      <h1>Spikes</h1>
      <p className="muted">
        Every spike alert is graded on what price did next: returns at +15/30/60/240 min, the best and worst move within
        240 min, and whether the suggested take-profit or stop was touched first. Net 60m subtracts a flat 1.5 points;
        net real subtracts each alert's own cost (spread at alert time + taker fees both ways). The micro row is shadow
        mode: spikes on coins under $1M/day, graded but never sent. Measurement only. Nothing here is traded.
      </p>
      <h2 style={{ fontSize: 16 }}>Scoreboard {day ? <span className="muted">({day})</span> : null}</h2>
      <div className="wrap">
        <table>
          <thead><tr>
            <th>Segment</th><th>n</th>
            <th>+15m mean / median</th><th>+30m</th><th>+60m</th><th>+240m</th><th>Net 60m</th><th>Net real</th><th>TP first</th><th>Stop first</th>
          </tr></thead>
          <tbody>
            {SEGMENTS.map(s => {
              const r = bySeg.get(s);
              if (!r) return null;
              const mm = (m: number | null, md: number | null) => <><span className={cls(m)}>{pct(m)}</span> / <span className={cls(md)}>{pct(md)}</span></>;
              return (
                <tr key={s}>
                  <td><strong>{s}</strong></td><td>{r.n}</td>
                  <td>{mm(r.mean_ret_15, r.median_ret_15)}</td><td>{mm(r.mean_ret_30, r.median_ret_30)}</td>
                  <td>{mm(r.mean_ret_60, r.median_ret_60)}</td><td>{mm(r.mean_ret_240, r.median_ret_240)}</td>
                  <td>{mm(r.mean_net_60, r.median_net_60)}</td>
                  <td>{mm(r.mean_net_60_real, r.median_net_60_real)}</td>
                  <td>{r.pct_tp_first == null ? "–" : `${r.pct_tp_first.toFixed(0)}%`}</td>
                  <td>{r.pct_stop_first == null ? "–" : `${r.pct_stop_first.toFixed(0)}%`}</td>
                </tr>
              );
            })}
            {bySeg.size === 0 && <tr><td colSpan={10} className="muted">No scoreboard yet. The Worker writes one daily at 04:00 UTC once alerts are graded.</td></tr>}
          </tbody>
        </table>
      </div>
      <h2 style={{ fontSize: 16 }}>Recent alerts</h2>
      <div className="wrap">
        <table>
          <thead><tr>
            <th>Fired</th><th>Symbol</th><th>Exch.</th><th>Move 30m</th><th>Vol ×</th><th>Liquidity</th><th>News</th>
            <th>+15m</th><th>+60m</th><th>+240m</th><th>MFE / MAE</th><th>First hit</th><th>Cost</th><th>Net real</th>
          </tr></thead>
          <tbody>
            {alerts.map(a => (
              <tr key={a.id}>
                <td>{new Date(a.fired_at).toLocaleString()}</td>
                <td><strong>{a.symbol}</strong>{a.shadow && <span className="muted"> · shadow</span>}</td><td>{a.exchange}</td>
                <td className="up">{pct(a.move_30m)}</td><td>{a.vol_multiple?.toFixed(1) ?? "–"}</td>
                <td>{a.liquidity_label ?? "–"}</td>
                <td className="muted">{a.has_news == null ? "?" : a.has_news ? (a.news_headline ?? "yes") : "none"}</td>
                <td className={cls(a.ret_15)}>{pct(a.ret_15)}</td>
                <td className={cls(a.ret_60)}>{pct(a.ret_60)}</td>
                <td className={cls(a.ret_240)}>{pct(a.ret_240)}</td>
                <td><span className="up">{pct(a.mfe_240)}</span> / <span className="down">{pct(a.mae_240)}</span></td>
                <td className={a.hit_tp_first ? "up" : a.hit_stop_first ? "down" : "muted"}>
                  {a.hit_tp_first ? "TP" : a.hit_stop_first ? "stop" : a.graded_complete ? "neither" : "…"}
                </td>
                <td className="muted">{a.cost_pct == null ? "–" : `${a.cost_pct.toFixed(1)}%`}</td>
                <td className={cls(a.net_60_real)}>{pct(a.net_60_real)}</td>
              </tr>
            ))}
            {alerts.length === 0 && <tr><td colSpan={14} className="muted">No spike alerts yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
