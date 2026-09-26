import { getStore } from "@netlify/blobs";

const SITES = new Set(["door", "creative-studio", "tech-studio", "tech-profile", "creative-consultancy"]);
const BOT = /bot|crawl|spider|headless|lighthouse|preview|monitor/i;
const clip = (s, n) => String(s || "").slice(0, n);
const num = (v, max) => Math.max(0, Math.min(Number(v) || 0, max));

export default async (req, context) => {
  if (req.method !== "POST") return new Response(null, { status: 405 });
  if (BOT.test(req.headers.get("user-agent") || "")) return new Response(null, { status: 204 });
  let b;
  try { b = JSON.parse(await req.text()); } catch { return new Response(null, { status: 400 }); }
  if (!b || !/^[a-z0-9]{6,40}$/.test(b.sid || "")) return new Response(null, { status: 400 });

  const store = getStore("sessions");
  const day = new Date().toISOString().slice(0, 10);
  const key = `${day}/${b.sid}`;
  const rec = (await store.get(key, { type: "json" })) || {
    t: Date.now(),
    c: clip(context.geo?.country?.code, 2) || "??",
    dev: b.dev === "mobile" ? "mobile" : "desktop",
    ref: clip(b.ref, 60),
    views: {}, ms: {}, sec: {},
  };

  const d = b.d || {};
  for (const [k, v] of Object.entries(d.views || {})) if (SITES.has(k)) rec.views[k] = (rec.views[k] || 0) + num(v, 20);
  for (const [k, v] of Object.entries(d.ms || {})) if (SITES.has(k)) rec.ms[k] = (rec.ms[k] || 0) + num(v, 60000);
  for (const [k, v] of Object.entries(d.sec || {})) {
    const [site, ...rest] = k.split("|");
    if (!SITES.has(site) || Object.keys(rec.sec).length > 150) continue;
    const name = `${site}|${clip(rest.join("|"), 50)}`;
    rec.sec[name] = (rec.sec[name] || 0) + num(v, 60000);
  }
  await store.setJSON(key, rec);
  return new Response(null, { status: 204 });
};

export const config = { path: "/api/track" };
