/** Scheduler for the Python scanner. GitHub Actions' own cron for this repo starts runs hours
 *  late or not at all, so this Worker's cron ("1-59/5 * * * *", i.e. minute 1, 6, 11, ...)
 *  starts them with workflow_dispatch, which GitHub runs within seconds. GitHub's scan cron
 *  stays as a backup (a duplicate scan is harmless: everything it sends is deduped). */
import type { Env } from "./config";
import { telegram } from "./services";

export const DISPATCH_CRON = "1-59/5 * * * *";
const KV_HEALTH = "dispatch_health";
const DOWN_AFTER = 3;

export type Dispatch = { workflow: string; inputs?: Record<string, string> };

/** Hour of day in Edmonton (MDT or MST, whichever is in force). */
export function edmontonHour(now: number): number {
  return Number(new Intl.DateTimeFormat("en-CA", { timeZone: "America/Edmonton", hour: "2-digit", hourCycle: "h23" }).format(now));
}

/** What to start at this tick. Minute 1 of every hour: everything (Stage A right after each hourly
 *  close, so 00:01 UTC catches the daily close). Minutes 16/31/46: Stage B + exits + listings.
 *  Otherwise listings only. Daily digest: minute 1 of the hour that is 07:00 in Edmonton. */
export function plan(now: number): Dispatch[] {
  const m = new Date(now).getUTCMinutes();
  const stage = m < 5 ? "all" : m % 15 < 5 ? "b,l" : "l";
  const out: Dispatch[] = [{ workflow: "scan.yml", inputs: { stage } }];
  if (m < 5 && edmontonHour(now) === 7) out.push({ workflow: "daily.yml" });
  return out;
}

export async function dispatch(env: Env, now: number): Promise<void> {
  if (!env.GH_DISPATCH_TOKEN) { console.log("[dispatch] GH_DISPATCH_TOKEN not set"); return; }
  const errors: string[] = [];
  for (const d of plan(now)) {
    try {
      const r = await fetch(`https://api.github.com/repos/${env.GH_REPO}/actions/workflows/${d.workflow}/dispatches`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`, Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "spike-detector-dispatch",
        },
        body: JSON.stringify({ ref: "master", ...(d.inputs ? { inputs: d.inputs } : {}) }),
      });
      if (r.status !== 204) errors.push(`${d.workflow}: HTTP ${r.status} ${(await r.text()).slice(0, 120)}`);
      else console.log(`[dispatch] ${d.workflow} ${JSON.stringify(d.inputs ?? {})}`);
    } catch (e) {
      errors.push(`${d.workflow}: ${e}`);
    }
  }
  await health(env, errors);
}

/** One Telegram line when dispatching has failed DOWN_AFTER ticks in a row, one when it recovers. */
async function health(env: Env, errors: string[]): Promise<void> {
  const h = (await env.SPIKE_KV.get<{ failures: number; down: boolean }>(KV_HEALTH, "json")) ?? { failures: 0, down: false };
  if (!errors.length) {
    if (h.down) await telegram(env, `*SCHEDULER RECOVERED*: the Worker is starting GitHub scans again (after ${h.failures} failed ticks).`);
    if (h.failures || h.down) await env.SPIKE_KV.put(KV_HEALTH, JSON.stringify({ failures: 0, down: false }));
    return;
  }
  console.log("[dispatch] failed:", errors.join(" | "));
  const next = { failures: h.failures + 1, down: h.down };
  if (next.failures >= DOWN_AFTER && !h.down) {
    await telegram(env, `*SCHEDULER DOWN*: the Worker could not start GitHub scans ${next.failures} times in a row (${errors[0]}).`);
    next.down = true;
  }
  await env.SPIKE_KV.put(KV_HEALTH, JSON.stringify(next));
}
