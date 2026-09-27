#!/usr/bin/env python3
"""
Generates crawlable, static HTML pages for the four dot. brands, extracting
real text straight out of the JSON-embedded content already in public/index.html
(no invented copy). Also emits robots.txt, sitemap.xml and llms.txt.

Run from the repo root:  python3 tools/build_static_pages.py
"""
import re, json, html, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "public", "index.html")
DOMAIN = "https://www.dot-cc.com"

BRANDS = {
    "creative-studio": dict(key="studio", path="creative-studio", color="#FF0000", on="#FFFFFF",
        title="dot. creative studio | brand identity & campaigns, Riyadh",
        desc="dot. creative studio builds brand strategy, identity and campaigns for companies in Saudi Arabia that are done playing it safe.",
        name="dot. creative studio"),
    "tech-studio": dict(key="tech", path="tech-studio", color="#00F4C9", on="#121D21",
        title="dot. tech studio | AI, business systems & data, Saudi Arabia",
        desc="dot. tech studio puts AI to work, builds business systems, moves and fixes data, and rescues stalled tech projects for companies in Saudi Arabia.",
        name="dot. tech studio"),
    "tech-profile": dict(key="profile", path="tech-studio-profile", color="#00F4C9", on="#121D21",
        title="dot. tech studio — company profile | Saudi Arabia",
        desc="Company profile: AI and automation, business systems, data, rescue and compliance, and technology leadership for companies in Saudi Arabia.",
        name="dot. tech studio"),
    "creative-consultancy": dict(key="cc", path="creative-consultancy", color="#0068FF", on="#FFFFFF",
        title="dot. creative consultancy | business + brand consulting, Riyadh",
        desc="dot. is a business consultancy with creative solutions: we find what is holding a company back, fix it, and give the company a story worth telling.",
        name="dot. creative consultancy"),
}

# Curated FAQ content — real facts confirmed by dot., not extracted mechanically.
# Add entries here as more real facts (pricing, timelines, terms) are confirmed.
PRICING_Q = "How much does it cost to work with {name}?"
PRICING_A = ("Engagements start at 3,750 SAR per month. The exact scope and price are set "
             "after an initial conversation about what you need.")
MANUAL_FAQS = {
    slug: [(PRICING_Q.format(name=b["name"]), PRICING_A)]
    for slug, b in BRANDS.items()
}

def load_sections():
    s = open(SRC, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'<script type="application/json" id="src-(\w+)">(.*?)</script>', s, re.S):
        out[m.group(1)] = json.loads(m.group(2))
    return out

def clean(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    h = re.sub(r'<span[^>]*lang="ar"[^>]*>.*?</span>', "", h, flags=re.S)
    return h

def extract(h):
    """Pull headings/paragraphs/list items in document order as (tag, text)."""
    items = []
    for m in re.finditer(r"<(h1|h2|h3|p|li)\b[^>]*>(.*?)</\1>", h, re.S):
        tag, txt = m.group(1), m.group(2)
        txt = re.sub(r"<[^>]+>", " ", txt)
        txt = html.unescape(txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt and len(txt) > 1:
            items.append((tag, txt))
    return items

def to_semantic_html(items):
    """Render the extracted (tag,text) stream as clean nested HTML, grouping
    list items into <ul> and demoting the page's own h1 to h2 (the static
    page supplies its own h1)."""
    out = []
    in_list = False
    first_h1_seen = False
    for tag, txt in items:
        if tag == "li":
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{html.escape(txt)}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if tag == "h1":
            if not first_h1_seen:
                first_h1_seen = True
                out.append(f"<p class=\"lead\">{html.escape(txt)}</p>")
            else:
                out.append(f"<h2>{html.escape(txt)}</h2>")
            continue
        out.append(f"<{tag}>{html.escape(txt)}</{tag}>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)

def faq_pairs(items):
    """Pick heading/paragraph pairs that already read like a question and
    answer, for FAQPage structured data. Purely mechanical — no invented
    text, only what already exists on the page."""
    pairs = []
    for i, (tag, txt) in enumerate(items):
        if tag in ("h2", "h3") and txt.strip().endswith("?") and len(txt) < 140:
            for j in range(i + 1, min(i + 4, len(items))):
                if items[j][0] == "p":
                    pairs.append((txt, items[j][1]))
                    break
    return pairs[:8]

PAGE_TMPL = """<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:site_name" content="dot.">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<link rel="icon" href="{domain}/favicon.ico">
{schema}
<style>
:root{{--ink:#141414;--mut:#5c5c58;--line:#e6e4de;--bg:#faf9f6;--accent:{color};--on:{on}}}
@media(prefers-color-scheme:dark){{:root{{--ink:#f2f1ee;--mut:#a8a89f;--line:#2c2c29;--bg:#0d0d0c}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}}
.wrap{{max-width:720px;margin:0 auto;padding:32px 20px 80px}}
header.top{{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:28px;flex-wrap:wrap}}
.brand{{font-weight:700;text-decoration:none;color:var(--ink);font-size:15px}}
.brand b{{color:var(--accent)}}
nav.crumbs{{font-size:13px;color:var(--mut)}}
nav.crumbs a{{color:var(--mut)}}
h1{{font-size:clamp(28px,5vw,42px);line-height:1.1;margin:0 0 10px}}
.lead{{font-size:19px;color:var(--mut);margin:0 0 28px}}
h2{{font-size:22px;margin:40px 0 10px}}
h3{{font-size:17px;margin:20px 0 6px}}
p{{margin:0 0 14px}}
ul{{margin:0 0 18px;padding-left:22px}}
li{{margin:0 0 8px}}
.cta{{display:inline-block;margin:36px 0 8px;padding:14px 26px;background:var(--accent);color:var(--on);text-decoration:none;font-weight:700;border-radius:8px}}
.foot{{margin-top:56px;padding-top:20px;border-top:1px solid var(--line);color:var(--mut);font-size:13px}}
.foot a{{color:var(--mut)}}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
<a class="brand" href="{domain}/">dot<b>.</b></a>
<nav class="crumbs"><a href="{domain}/">dot.</a> / {name}</nav>
</header>
<main>
<h1>{h1}</h1>
{body}
<a class="cta" href="{domain}/#{hash}">Open the full interactive site &rarr;</a>
</main>
<div class="foot">
<p>{name}, part of dot. &mdash; Riyadh, Saudi Arabia. <a href="mailto:info@dot-cs.com">info@dot-cs.com</a></p>
<p><a href="{domain}/">dot. home</a> &middot; <a href="{domain}/creative-studio/">creative studio</a> &middot; <a href="{domain}/tech-studio/">tech studio</a> &middot; <a href="{domain}/tech-studio-profile/">tech studio profile</a> &middot; <a href="{domain}/creative-consultancy/">creative consultancy</a></p>
</div>
</div>
</body>
</html>
"""

def build():
    sections = load_sections()
    urls = []
    for slug, b in BRANDS.items():
        html_src = clean(sections[b["key"]])
        items = extract(html_src)
        h1 = next((t for tag, t in items if tag == "h1"), b["name"])
        body = to_semantic_html(items)
        url = f"{DOMAIN}/{b['path']}/"
        faqs = faq_pairs(items) + MANUAL_FAQS.get(slug, [])
        faq_html = "\n".join(
            f"<h3>{html.escape(q)}</h3>\n<p>{html.escape(a)}</p>" for q, a in MANUAL_FAQS.get(slug, [])
        )
        if faq_html:
            body += f"\n<h2>Pricing</h2>\n{faq_html}"
        schema_blocks = [{
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": b["title"],
            "description": b["desc"],
            "url": url,
            "isPartOf": {"@type": "WebSite", "name": "dot.", "url": DOMAIN},
            "about": {"@type": "Organization", "name": b["name"]},
        }]
        if faqs:
            schema_blocks.append({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q,
                     "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in faqs
                ],
            })
        schema = "\n".join(
            f'<script type="application/ld+json">{json.dumps(sb, ensure_ascii=False)}</script>'
            for sb in schema_blocks
        )
        page = PAGE_TMPL.format(
            title=html.escape(b["title"]), desc=html.escape(b["desc"]),
            url=url, domain=DOMAIN, color=b["color"], on=b["on"],
            name=html.escape(b["name"]), h1=html.escape(h1), body=body,
            hash=slug, schema=schema,
        )
        outdir = os.path.join(ROOT, "public", b["path"])
        os.makedirs(outdir, exist_ok=True)
        open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
        urls.append((url, len(page)))
        print(f"wrote public/{b['path']}/index.html ({len(page)} bytes, {len(faqs)} FAQ pairs)")

    # sitemap.xml
    today = datetime.date.today().isoformat()
    all_urls = [f"{DOMAIN}/"] + [u for u, _ in urls]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in all_urls:
        sm.append(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "public", "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    print("wrote public/sitemap.xml")

    # robots.txt
    robots = f"""User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
"""
    open(os.path.join(ROOT, "public", "robots.txt"), "w").write(robots)
    print("wrote public/robots.txt")

    # llms.txt — AEO: a plain-language summary for AI assistants / answer engines
    llms = f"""# dot.

> dot. is a Riyadh-based group of three businesses that work together: a creative studio, a tech studio, and a creative consultancy that combines both. It serves companies in Saudi Arabia.

## Businesses

- [dot. creative studio]({DOMAIN}/creative-studio/): brand strategy, identity, and advertising campaigns.
- [dot. tech studio]({DOMAIN}/tech-studio/): AI and automation, business systems, data, and rescuing stalled technology projects, for regulated industries such as insurance and payments in Saudi Arabia.
- [dot. tech studio — company profile]({DOMAIN}/tech-studio-profile/): the full company profile for dot. tech studio.
- [dot. creative consultancy]({DOMAIN}/creative-consultancy/): a business consultancy with creative solutions — finds what is holding a company back, fixes it, and builds the story to tell about it.

## Pricing

Engagements across all three businesses start at 3,750 SAR per month. Exact scope and price are set after an initial conversation.

## Contact

- Email: info@dot-cs.com
- Location: Riyadh, Saudi Arabia
- Website: {DOMAIN}

## Notes for automated readers

Each business above has its own page with full detail; the homepage ({DOMAIN}/) is an interactive front door that links to all of them.
"""
    open(os.path.join(ROOT, "public", "llms.txt"), "w").write(llms)
    print("wrote public/llms.txt")

if __name__ == "__main__":
    build()
