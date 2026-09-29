// Pages render on the server (UTC on Vercel), so format times in the owner's zone explicitly.
const TZ = "America/Edmonton";

export const fmtDateTime = (iso: string) =>
  new Date(iso).toLocaleString("en-CA", { timeZone: TZ, dateStyle: "medium", timeStyle: "short" });
export const fmtDate = (iso: string) => new Date(iso).toLocaleDateString("en-CA", { timeZone: TZ });
