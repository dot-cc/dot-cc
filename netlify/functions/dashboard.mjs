import { getStore } from "@netlify/blobs";

const NAMES = {
  door: "Front door",
  "creative-studio": "Creative studio",
  "tech-studio": "Tech studio",
  "tech-profile": "Tech company profile",
  "creative-consultancy": "Creative consultancy",
};
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (ms) => {
  const s = Math.round(ms / 1000);
  return s < 60 ? `${s}s` : s < 3600 ? `${Math.floor(s / 60)}m ${s % 60}s` : `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
};

async function loadAll(store, days) {
  const out = [];
  for (const day of days) {
    const { blobs } = await store.list({ prefix: day + "/" });
    for (let i = 0; i < blobs.length; i += 40) {
      const recs = await Promise.all(blobs.slice(i, i + 40).map((b) => store.get(b.key, { type: "json" })));
      recs.forEach((r) => r && out.push({ ...r, day }));
    }
  }
  return out;
}

const bars = (rows, fmtVal = (v) => v) => {
  const max = Math.max(1, ...rows.map((r) => r[1]));
  return rows.length
    ? rows.map(([l, v, sub]) => `<div class="row"><div class="lbl">${esc(l)}${sub ? `<small>${esc(sub)}</small>` : ""}</div><div class="bar"><i style="width:${(v / max) * 100}%"></i></div><b>${fmtVal(v)}</b></div>`).join("")
    : `<p class="empty">No data yet.</p>`;
};

export default async (req) => {
  const url = new URL(req.url);
  const key = process.env.DASH_KEY;
  if (!key || url.searchParams.get("key") !== key) return new Response("Not found", { status: 404 });

  const range = [7, 30, 90].includes(+url.searchParams.get("days")) ? +url.searchParams.get("days") : 30;
  const days = [...Array(range)].map((_, i) => new Date(Date.now() - i * 864e5).toISOString().slice(0, 10)).reverse();
  const sessions = await loadAll(getStore("sessions"), days);
  const allSubs = await loadAll(getStore("submissions"), days);
  const subs = allSubs.filter((s) => !s.test);
  const testSubs = allSubs.filter((s) => s.test);

  const visits = sessions.length;
  const totalMs = sessions.reduce((a, s) => a + Object.values(s.ms).reduce((x, y) => x + y, 0), 0);
  const byDay = Object.fromEntries(days.map((d) => [d, 0]));
  sessions.forEach((s) => byDay[s.day]++);
  const subByDay = Object.fromEntries(days.map((d) => [d, 0]));
  subs.forEach((s) => subByDay[s.day]++);

  const siteAgg = {};
  Object.keys(NAMES).forEach((k) => (siteAgg[k] = { ms: 0, views: 0, vis: 0 }));
  sessions.forEach((s) => {
    for (const k of Object.keys(NAMES)) {
      if (s.ms[k] || s.views[k]) siteAgg[k].vis++;
      siteAgg[k].ms += s.ms[k] || 0;
      siteAgg[k].views += s.views[k] || 0;
    }
  });
  const secAgg = {};
  sessions.forEach((s) => { for (const [k, v] of Object.entries(s.sec)) { (secAgg[k] ||= { ms: 0, n: 0 }); secAgg[k].ms += v; secAgg[k].n++; } });
  const count = (arr, f) => { const m = {}; arr.forEach((x) => { const k = f(x); if (k) m[k] = (m[k] || 0) + 1; }); return Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, 6); };
  const subSrc = count(subs, (s) => s.source);
  const recent = subs.sort((a, b) => b.ts - a.ts).slice(0, 8);

  const chart = (obj) => {
    const max = Math.max(1, ...Object.values(obj));
    return `<div class="spark">${days.map((d) => `<i title="${d}: ${obj[d]}" style="height:${Math.max(3, (obj[d] / max) * 100)}%"></i>`).join("")}</div>`;
  };
  const sites = Object.entries(siteAgg).filter(([, v]) => v.ms || v.views).sort((a, b) => b[1].ms - a[1].ms);
  const secs = Object.entries(secAgg).sort((a, b) => b[1].ms - a[1].ms).slice(0, 12);
  const link = (d) => `?key=${encodeURIComponent(key)}&days=${d}`;

  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>dot. dashboard</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#141414;--mut:#6b6b66;--line:#e5e3dd;--red:#ff0000}
@media(prefers-color-scheme:dark){:root{--bg:#0e0e0e;--card:#181818;--ink:#f2f1ee;--mut:#9a9a94;--line:#2a2a28}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0}h1 span{color:var(--red)}header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:20px}
nav a{color:var(--mut);text-decoration:none;padding:6px 12px;border:1px solid var(--line);border-radius:99px;margin-left:6px;font-size:13px}nav a.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.kpi small,.card h2{color:var(--mut);font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin:0}
.kpi b{display:block;font-size:34px;line-height:1.15;margin-top:4px}
.spark{display:flex;align-items:flex-end;gap:2px;height:44px;margin-top:10px}.spark i{flex:1;background:var(--red);border-radius:2px 2px 0 0;min-width:1px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:12px;margin-top:12px}
.row{display:grid;grid-template-columns:minmax(110px,38%) 1fr auto;gap:10px;align-items:center;padding:7px 0;font-size:14px}
.lbl small{display:block;color:var(--mut);font-size:11.5px}.bar{height:8px;background:var(--line);border-radius:9px;overflow:hidden}.bar i{display:block;height:100%;background:var(--red)}
.card h2{margin-bottom:8px}.empty,.foot{color:var(--mut);font-size:13px}ul{list-style:none;margin:0;padding:0}li{display:flex;justify-content:space-between;padding:6px 0;border-top:1px solid var(--line);font-size:14px}li span{color:var(--mut)}
@media(max-width:420px){.grid{grid-template-columns:1fr}}
</style></head><body><main>
<header><h1>dot.<span> </span>dashboard</h1><nav>${[7, 30, 90].map((d) => `<a class="${d === range ? "on" : ""}" href="${link(d)}">${d} days</a>`).join("")}</nav></header>
<div class="kpis">
<div class="card kpi"><small>Visits</small><b>${visits}</b>${chart(byDay)}</div>
<div class="card kpi"><small>Form submissions</small><b>${subs.length}</b>${chart(subByDay)}</div>
<div class="card kpi"><small>Avg time on site</small><b>${visits ? fmt(totalMs / visits) : "-"}</b><span class="foot">${visits ? ((subs.length / visits) * 100).toFixed(1) : 0}% of visits send a form</span></div>
<div class="card kpi"><small>Test submissions</small><b>${testSubs.length}</b><span class="foot">QA checks, excluded from the count above</span></div>
</div>
<div class="grid">
<div class="card"><h2>Where time is spent: sites</h2>${bars(sites.map(([k, v]) => [NAMES[k], v.ms, `${v.vis} visits, avg ${v.vis ? fmt(v.ms / v.vis) : "-"}`]), fmt)}</div>
<div class="card"><h2>Where time is spent: sections</h2>${bars(secs.map(([k, v]) => { const [s, ...r] = k.split("|"); return [r.join("|"), v.ms, `${NAMES[s]}, avg ${fmt(v.ms / v.n)}`]; }), fmt)}</div>
<div class="card"><h2>Traffic sources</h2>${bars(count(sessions, (s) => s.ref || "Direct"))}</div>
<div class="card"><h2>Countries</h2>${bars(count(sessions, (s) => s.c))}</div>
<div class="card"><h2>Devices</h2>${bars(count(sessions, (s) => s.dev))}</div>
<div class="card"><h2>Submissions by form</h2>${bars(subSrc)}<h2 style="margin-top:14px">Latest</h2>${recent.length ? `<ul>${recent.map((s) => `<li>${esc(s.source)}<span>${new Date(s.ts).toLocaleString("en-GB", { timeZone: "Asia/Riyadh", dateStyle: "medium", timeStyle: "short" })}</span></li>`).join("")}</ul>` : `<p class="empty">None yet.</p>`}</div>
</div>
<p class="foot">A visit is one browser session. Time counts only while the page is open, visible and being used. Times are in Riyadh time. Your own browser is excluded from counts after you open this page once.</p>
</main><script>try{localStorage.setItem("dot_notrack","1")}catch(e){}</script></body></html>`;
  return new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex" } });
};

export const config = { path: "/dashboard" };
