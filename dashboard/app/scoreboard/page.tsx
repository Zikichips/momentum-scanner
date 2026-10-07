import { supabase, type Scoreboard, type Alert } from "@/lib/supabase";

export const revalidate = 300;

export default async function ScoreboardPage() {
  const [{ data: sb }, { data: al }] = await Promise.all([
    supabase.from("scoreboard_daily").select("*").order("day", { ascending: false }).limit(60),
    supabase.from("alerts").select("outcome,r_multiple,rule_return,hold_7d_return,symbol,entry_type,taken,source").not("outcome", "is", null).not("outcome", "in", "(open,skipped_concurrent)").not("stale", "is", true),
  ]);
  const rows = (sb ?? []) as Scoreboard[];
  const latest = rows[0];
  const graded = (al ?? []) as Alert[];
  const byOutcome = ["t2", "t1", "stop", "expired"].map(o => ({ o, n: graded.filter(a => a.outcome === o).length }));

  const Tile = ({ k, v, c }: { k: string; v: string; c?: string }) => (
    <div className="tile"><div className="k">{k}</div><div className={`v ${c ?? ""}`}>{v}</div></div>
  );
  const pct = (v: number | null | undefined) => v == null ? "–" : `${(v * 100).toFixed(0)}%`;
  const avg = (xs: number[]) => xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : null;
  // Same definitions as outcomes.scoreboard(); alerts from before entry types count as pullback.
  const stats = (label: string, g: Alert[]) => {
    const rs = g.flatMap(a => a.r_multiple == null ? [] : [a.r_multiple]);
    const rules = avg(g.flatMap(a => a.rule_return == null ? [] : [a.rule_return]));
    const holds = avg(g.flatMap(a => a.hold_7d_return == null ? [] : [a.hold_7d_return]));
    return {
      t: label, n: g.length,
      winRate: g.length ? g.filter(a => (a.r_multiple ?? 0) > 0).length / g.length : null,
      avgR: avg(rs),
      vsHold: rules != null && holds != null ? rules - holds : null,
    };
  };
  // Listing alerts (pullbacks on coins the listing watcher put in play) are their own group.
  const group = (a: Alert) => a.source === "listing" ? "listing" : a.entry_type ?? "pullback";
  const byType = (["pullback", "breakout", "listing"] as const).map(t => stats(t, graded.filter(a => group(a) === t)));
  // Tool = every alert the scanner fired (including ones skipped at max positions);
  // trader = only the alerts actually taken.
  const toolVsTrader = [stats("tool (every alert)", graded), stats("trader (taken only)", graded.filter(a => a.taken !== false))];

  return (
    <>
      <h1>Scoreboard</h1>
      <p className="muted">Grades every alert the scanner fires, whether or not you traded it. Judge the tool after 30+ graded alerts, not before.</p>
      <div className="tiles">
        <Tile k="Alerts graded" v={String(latest?.alerts_graded ?? 0)} />
        <Tile k="Win rate" v={pct(latest?.win_rate)} c={(latest?.win_rate ?? 0) >= 0.4 ? "up" : "down"} />
        <Tile k="Avg R" v={latest?.avg_r?.toFixed(2) ?? "–"} c={(latest?.avg_r ?? 0) > 0 ? "up" : "down"} />
        <Tile k="Rules vs hold 7d" v={latest?.vs_hold_7d == null ? "–" : `${latest.vs_hold_7d > 0 ? "+" : ""}${latest.vs_hold_7d.toFixed(1)}pp`} c={(latest?.vs_hold_7d ?? 0) > 0 ? "up" : "down"} />
        {byOutcome.map(b => <Tile key={b.o} k={`Hit ${b.o.toUpperCase()}`} v={String(b.n)} />)}
      </div>
      <h2 style={{ fontSize: 16 }}>By entry type</h2>
      <div className="wrap">
        <table>
          <thead><tr><th>Entry</th><th>n</th><th>Win rate</th><th>Avg R</th><th>Expectancy (R/trade)</th><th>vs hold 7d</th></tr></thead>
          <tbody>
            {byType.map(r => (
              <tr key={r.t}>
                <td><strong>{r.t}</strong></td><td>{r.n}</td><td>{pct(r.winRate)}</td>
                <td className={r.avgR == null ? "muted" : r.avgR > 0 ? "up" : "down"}>{r.avgR?.toFixed(2) ?? "–"}</td>
                <td className={r.avgR == null ? "muted" : r.avgR > 0 ? "up" : "down"}>{r.avgR?.toFixed(2) ?? "–"}</td>
                <td className={r.vsHold == null ? "muted" : r.vsHold > 0 ? "up" : "down"}>{r.vsHold == null ? "–" : `${r.vsHold > 0 ? "+" : ""}${r.vsHold.toFixed(1)}pp`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2 style={{ fontSize: 16 }}>Tool vs trader</h2>
      <div className="wrap">
        <table>
          <thead><tr><th></th><th>n</th><th>Win rate</th><th>Avg R</th><th>Expectancy (R/trade)</th><th>vs hold 7d</th></tr></thead>
          <tbody>
            {toolVsTrader.map(r => (
              <tr key={r.t}>
                <td><strong>{r.t}</strong></td><td>{r.n}</td><td>{pct(r.winRate)}</td>
                <td className={r.avgR == null ? "muted" : r.avgR > 0 ? "up" : "down"}>{r.avgR?.toFixed(2) ?? "–"}</td>
                <td className={r.avgR == null ? "muted" : r.avgR > 0 ? "up" : "down"}>{r.avgR?.toFixed(2) ?? "–"}</td>
                <td className={r.vsHold == null ? "muted" : r.vsHold > 0 ? "up" : "down"}>{r.vsHold == null ? "–" : `${r.vsHold > 0 ? "+" : ""}${r.vsHold.toFixed(1)}pp`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2 style={{ fontSize: 16 }}>Daily history</h2>
      <div className="wrap">
        <table>
          <thead><tr><th>Day</th><th>Total</th><th>Graded</th><th>Wins</th><th>Losses</th><th>Win rate</th><th>Avg R</th><th>vs hold 7d</th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.day}>
                <td>{r.day}</td><td>{r.alerts_total}</td><td>{r.alerts_graded}</td><td className="up">{r.wins}</td><td className="down">{r.losses}</td>
                <td>{pct(r.win_rate)}</td><td>{r.avg_r?.toFixed(2) ?? "–"}</td><td>{r.vs_hold_7d?.toFixed(1) ?? "–"}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={8} className="muted">No scoreboard rows yet. The daily job writes one per day.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
