// Supabase REST, Telegram and best-effort enrichment (CryptoPanic, Reddit). Every enrichment
// call has a short timeout and returns null on any failure: it must never block an alert.
import type { Env } from "./config";
import { findHeadline, type Feeds } from "./news";

const T = (ms: number) => AbortSignal.timeout(ms);

// ------------------------------------------------------------------ Supabase
export const hasSupabase = (env: Env) => !!(env.SUPABASE_URL && env.SUPABASE_SERVICE_ROLE_KEY);

export async function sb(env: Env, path: string, init: RequestInit = {}): Promise<any> {
  const r = await fetch(`${env.SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    signal: T(10_000),
    headers: {
      apikey: env.SUPABASE_SERVICE_ROLE_KEY!,
      Authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  if (!r.ok) throw new Error(`supabase ${r.status}: ${(await r.text()).slice(0, 200)}`);
  return r.status === 204 ? null : r.json();
}

// ------------------------------------------------------------------ Telegram
export async function telegram(env: Env, text: string): Promise<void> {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) {
    console.log(`[telegram disabled]\n${text}`);
    return;
  }
  // Plain text (no parse_mode): symbols and headlines can contain Markdown characters.
  const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST", signal: T(10_000),
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text, disable_web_page_preview: true }),
  });
  if (!r.ok) console.log("telegram failed", r.status, await r.text());
}

// ------------------------------------------------------------------ enrichment
/** Newest headline in the last 6h mentioning the coin. CryptoPanic when a token is set (paid
 *  "growth" API; the free v1 API now returns 403), otherwise the free RSS feeds in news.ts.
 *  checked = false when no source answered, so has_news is stored as unknown, not "no". */
export async function newsHeadline(env: Env, base: string, name: string | undefined, now: number,
                                   feeds: () => Promise<Feeds>): Promise<{ checked: boolean; headline: string | null }> {
  if (env.CRYPTOPANIC_TOKEN) {
    try {
      const r = await fetch(`${env.CRYPTOPANIC_URL}?auth_token=${env.CRYPTOPANIC_TOKEN}&currencies=${base}&public=true`, { signal: T(4000) });
      if (r.ok) {
        const json: any = await r.json();
        const hit = (json.results ?? []).find((p: any) => now - Date.parse(p.published_at) <= 6 * 3600_000);
        return { checked: true, headline: hit ? String(hit.title).slice(0, 140) : null };
      }
      console.log("cryptopanic", r.status, "- falling back to RSS");
    } catch (err) {
      console.log("cryptopanic failed - falling back to RSS:", String(err));
    }
  }
  try {
    const f = await feeds();
    if (f.ok === 0) return { checked: false, headline: null };
    const hit = findHeadline(f.items, base, name, now);
    return { checked: true, headline: hit ? `${hit.title.slice(0, 140)} (${hit.source})` : null };
  } catch {
    return { checked: false, headline: null };
  }
}

/** Reddit posts mentioning the symbol in the last 24h vs the 7-day daily average, across
 *  r/CryptoCurrency and r/{base}. Reddit's OAuth API directly (praw is Python-only). Each search
 *  returns at most 100 posts, so very busy symbols are undercounted. */
export async function redditMentions(env: Env, base: string, now: number): Promise<{ m24: number; avg7d: number } | null> {
  if (!env.REDDIT_CLIENT_ID || !env.REDDIT_CLIENT_SECRET) return null;
  const ua = "spike-detector/1.0 (measurement bot)";
  try {
    const tok = await fetch("https://www.reddit.com/api/v1/access_token", {
      method: "POST", signal: T(4000),
      headers: { Authorization: `Basic ${btoa(`${env.REDDIT_CLIENT_ID}:${env.REDDIT_CLIENT_SECRET}`)}`,
                 "Content-Type": "application/x-www-form-urlencoded", "User-Agent": ua },
      body: "grant_type=client_credentials",
    });
    if (!tok.ok) return null;
    const { access_token } = await tok.json<any>();
    const subs = ["CryptoCurrency", base];
    const res = await Promise.allSettled(subs.map(s => fetch(
      `https://oauth.reddit.com/r/${s}/search?q=${encodeURIComponent(base)}&restrict_sr=1&sort=new&t=week&limit=100`,
      { signal: T(4000), headers: { Authorization: `Bearer ${access_token}`, "User-Agent": ua } })
      .then(r => r.ok ? r.json<any>() : null)));
    const times: number[] = [];
    for (const r of res) if (r.status === "fulfilled" && r.value)
      for (const c of r.value.data?.children ?? []) times.push(c.data.created_utc * 1000);
    const m24 = times.filter(t => now - t <= 24 * 3600_000).length;
    const week = times.filter(t => now - t <= 7 * 24 * 3600_000).length;
    return { m24, avg7d: week / 7 };
  } catch {
    return null;
  }
}

/** Earlier spike alerts for this symbol in the last 90 days and their average +60-min return. */
export async function priorSpikes(env: Env, base: string, now: number): Promise<{ n: number; avgRet60: number | null }> {
  if (!hasSupabase(env)) return { n: 0, avgRet60: null };
  try {
    const since = new Date(now - 90 * 86_400_000).toISOString();
    const rows: { ret_60: number | null }[] = await sb(env, `spike_alerts?symbol=eq.${base}&kind=eq.spike&fired_at=gte.${since}&select=ret_60`);
    const r60 = rows.map(r => r.ret_60).filter((x): x is number => x != null);
    return { n: rows.length, avgRet60: r60.length ? r60.reduce((s, x) => s + x, 0) / r60.length : null };
  } catch {
    return { n: 0, avgRet60: null };
  }
}
