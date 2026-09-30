#!/usr/bin/env python3
"""Send people who land on the static text pages to the interactive site.

The static pages exist so search engines and AI assistants can read the site.
People should end up in the interactive version, which has the working forms,
lead tracking and the full experience. This script adds two things to every
static page (idempotent, safe to re-run after rebuilding pages):

1. A banner under the header with a button to the matching interactive studio,
   in the page's language. Seen by everyone, including crawlers.
2. A small script that sends visitors straight there when they arrive from an
   AI assistant (ChatGPT, Perplexity, Claude, Gemini, Copilot ...), detected by
   referrer or utm_source. Crawlers send no referrer, so they always read the
   static page. Add ?text=1 to a URL to stay on the text version.

Search-engine visitors (Google, Bing) are not redirected; they see the banner.
"""
import glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://www.dot-cc.com"
SKIP = {"thanks", "privacy"}

# static path (without /ar/ prefix) -> interactive route
ROUTES = {
    "tech-studio": "tech-studio",
    "tech-studio-results": "tech-studio",
    "tech-studio-profile": "tech-profile",
    "creative-studio": "creative-studio",
    "creative-consultancy": "creative-consultancy",
    "case-studies": "tech-studio",
    "contact": "",
    "": "",
}
TEXT = {
    "en": ("You are reading the text version of this page.", "Open the interactive site &rarr;"),
    "ar": ("أنت تقرأ النسخة النصية من هذه الصفحة.", "افتح الموقع التفاعلي &larr;"),
}

CSS = """/* handoff:start */
.handoff{display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;margin:0 0 20px;padding:12px 16px;border:1px solid var(--line);border-radius:14px;background:var(--bg)}
.handoff span{color:var(--mut);font-size:14px}
.handoff a{display:inline-block;padding:9px 18px;background:var(--accent);color:var(--on);text-decoration:none;font-weight:700;border-radius:999px;font-size:14px}
.handoff a:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
/* the spam-trap field sat at left:-9999px, which adds ~10,000px of sideways scroll on right-to-left (Arabic) pages */
.lf-hp{left:0;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);opacity:0}
/* handoff:end */
"""

SCRIPT = """<!-- handoff-script:start -->
<script>(function(){
  var btn=document.getElementById("handoff-btn"); if(!btn) return;
  function setLang(){ try{ localStorage.setItem("dot-lang",btn.getAttribute("data-lang")); localStorage.setItem("dotLang",btn.getAttribute("data-lang")); }catch(e){} }
  btn.addEventListener("click",setLang);
  var q=location.search, host="";
  try{ host=new URL(document.referrer).hostname; }catch(e){}
  var fromAI=/(^|\\.)(chatgpt\\.com|chat\\.openai\\.com|perplexity\\.ai|claude\\.ai|gemini\\.google\\.com|copilot\\.microsoft\\.com|you\\.com|poe\\.com)$/i.test(host)
    || /[?&]utm_source=(chatgpt\\.com|perplexity|copilot|gemini|claude)/i.test(q);
  if(fromAI && btn.getAttribute("data-auto")!=="0" && !/[?&]text=1(&|$)/.test(q)){ setLang(); location.replace(btn.href); }
})();</script>
<!-- handoff-script:end -->
"""


def route_for(path_rel):
    parts = [p for p in path_rel.split("/") if p]
    lang = "ar" if parts and parts[0] == "ar" else "en"
    if lang == "ar":
        parts = parts[1:]
    key = parts[0] if parts else ""
    return lang, ROUTES.get(key)


def patch(path):
    rel = os.path.relpath(os.path.dirname(path), os.path.join(ROOT, "public"))
    rel = "" if rel == "." else rel
    parts = [p for p in rel.split("/") if p]
    if any(p in SKIP for p in parts):
        return False
    lang, route = route_for(rel)
    if route is None:
        return False
    h = open(path, encoding="utf-8").read()
    # strip any earlier version
    h = re.sub(r"/\* handoff:start \*/.*?/\* handoff:end \*/\n", "", h, flags=re.S)
    h = re.sub(r'<aside class="handoff".*?</aside>\n?', "", h, flags=re.S)
    h = re.sub(r"<!-- handoff-script:start -->.*?<!-- handoff-script:end -->\n?", "", h, flags=re.S)
    target = f"{DOMAIN}/#{route}" if route else f"{DOMAIN}/"
    note, label = TEXT[lang]
    # The interactive creative studio is English-only: keep Arabic readers on the
    # Arabic text (no automatic hand-off), but still offer the button.
    auto = "" if not (lang == "ar" and route == "creative-studio") else ' data-auto="0"'
    banner = (f'<aside class="handoff"><span>{note}</span>'
              f'<a id="handoff-btn" data-lang="{lang}"{auto} href="{target}">{label}</a></aside>\n')
    if "</style>" not in h or "</header>" not in h or "</body>" not in h:
        return False
    h = h.replace("</style>", CSS + "</style>", 1)
    h = h.replace("</header>\n", "</header>\n" + banner, 1)
    h = h.replace("</body>", SCRIPT + "</body>", 1)
    open(path, "w", encoding="utf-8").write(h)
    return True


def main():
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "public", "**", "index.html"), recursive=True)):
        if os.path.dirname(f) == os.path.join(ROOT, "public"):
            continue  # the interactive site itself
        n += patch(f)
    print(f"handoff added to {n} pages")


if __name__ == "__main__":
    main()
