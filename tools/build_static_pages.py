#!/usr/bin/env python3
"""
Generates crawlable, static HTML pages for the four dot. brands, extracting
real text straight out of the JSON-embedded content already in public/index.html
(no invented copy) — in English, and in Arabic wherever the source already
carries a real Arabic version of that content. Also emits robots.txt,
sitemap.xml and llms.txt.

Bilingual handling, by brand (this is how the source actually stores it,
verified before writing this script — not assumed):
  - tech-studio / tech-profile: content is tagged with data-i18n="key"
    attributes; a `const AR = {...}` object holds the real Arabic string for
    each key, and a separate `const DATA = {en:{...}, ar:{...}}` object holds
    the bilingual "client results" case list.
  - creative-consultancy: English and Arabic text sit side by side as sibling
    <span class="en"> / <span class="ar" lang="ar"> elements in the same markup.
  - creative-studio: the live interactive site is English only — it has no
    bilingual markup to extract. Its Arabic static page (below) is instead a
    curated, hand-translated mirror of the same real English content pulled
    from the source (CREATIVE_STUDIO_AR), following the same precedent as
    build_ar_home_page: composed by hand because the source has nothing to
    extract, not invented content.

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
        name="dot. creative studio", i18n="manual"),
    "tech-studio": dict(key="tech", path="tech-studio", color="#00F4C9", on="#121D21",
        title="dot. tech studio | AI, business systems & data, Saudi Arabia",
        desc="dot. tech studio puts AI to work, builds business systems, moves and fixes data, and rescues stalled tech projects for companies in Saudi Arabia.",
        name="dot. tech studio", i18n="dict"),
    "tech-profile": dict(key="profile", path="tech-studio-profile", color="#00F4C9", on="#121D21",
        title="dot. tech studio — company profile | Saudi Arabia",
        desc="Company profile: AI and automation, business systems, data, rescue and compliance, and technology leadership for companies in Saudi Arabia.",
        name="dot. tech studio", i18n="dict"),
    "creative-consultancy": dict(key="cc", path="creative-consultancy", color="#0068FF", on="#FFFFFF",
        title="dot. creative consultancy | business + brand consulting, Riyadh",
        desc="dot. is a business consultancy with creative solutions: we find what is holding a company back, fix it, and give the company a story worth telling.",
        name="dot. creative consultancy", i18n="spans"),
}

# Curated FAQ content — real facts confirmed by dot., not extracted mechanically.
PRICING_Q = "How much does it cost to work with {name}?"
PRICING_A = ("Engagements start at 3,750 SAR per month. The exact scope and price are set "
             "after an initial conversation about what you need.")
MANUAL_FAQS = {slug: [(PRICING_Q.format(name=b["name"]), PRICING_A)] for slug, b in BRANDS.items()}

# Arabic versions of the same curated facts. Composed by hand (not extracted),
# following the source's own convention of keeping the Latin brand name as-is
# inside an Arabic sentence.
PRICING_Q_AR = "كم تبلغ تكلفة العمل مع {name}؟"
PRICING_A_AR = "تبدأ المشاريع من 3,750 ريال سعودي شهريًا. يُحدَّد النطاق والسعر الدقيقان بعد محادثة أولى حول ما تحتاجه."
MANUAL_FAQS_AR = {slug: [(PRICING_Q_AR.format(name=b["name"]), PRICING_A_AR)] for slug, b in BRANDS.items()}

# ---------------------------------------------------------------------------
# creative-studio has no bilingual markup in the source to extract (see the
# module docstring). Its Arabic page is a curated, hand-translated mirror of
# the real English content above, in the same document order, following the
# same "composed by hand, not extracted" precedent as build_ar_home_page and
# MANUAL_FAQS_AR. Case/project names (Omnisphere, Al Saif Brands, etc.) are
# proper nouns and are kept in Latin script, matching how "dot." itself and
# other brand names stay Latin inside Arabic copy elsewhere on the site.
# ---------------------------------------------------------------------------
CREATIVE_STUDIO_AR_TITLE = "dot. creative studio | هوية العلامة التجارية والحملات، الرياض"
CREATIVE_STUDIO_AR_DESC = ("استوديو dot. الإبداعي يبني استراتيجية العلامة التجارية وهويتها وحملاتها "
                            "لشركات في السعودية سئمت من اللعب بأمان.")

_CS_CASES_AR = [
    ("Omnisphere", "تمت تسميتها وبناؤها من الصفر. نظام علامة تجارية واحد يهتدي بنجمة، يجمع ثلاثة أعمال: الإنتاج، والمقاولات، والاستشارات."),
    ("Al Saif Brands", "عائلة واحدة، وثلاثة خطوط: الفخامة، والبيع النقدي بالجملة (Cash & Carry)، وقطاع الضيافة HORECA (الفنادق والمطاعم والمقاهي). هوية، ووسائل تواصل اجتماعي، وأجنحة معارض."),
    ("Al Dahayan", "إعادة تسمية للعلامة، وأجنحة معارض، وحملات بحجم يليق بإحدى أبرز مصانع تكسية الألمنيوم في السعودية."),
    ("Fakhda & Bas", "إعادة علامة تجارية كاملة لمطبخ سحابي سعودي متخصص في توصيل اللحوم الفاخرة. حيث يلتقي التراث الطهي بسرعة التوصيل، عبر التغليف ووسائل التواصل الاجتماعي."),
    ("Awan", "هوية لشركة سلاسل إمداد تُحوّل الشحن والتخزين إلى لغة علامة تجارية تتحدث عن الحركة والموثوقية."),
    ("Silver in Sky", "هوية سماوية لأدوات الضيافة الفضية الفاخرة، إضافة إلى قطع فضية صممناها ونُفّذت بالفعل وباتت على موائد المطاعم الراقية."),
    ("Monarque", "تمت تسميتها وبناؤها منذ أول رسم تخطيطي: علامة تجارية لتوريد مستلزمات الفنادق والمطاعم تحمل الهيبة التي يعد بها اسمها."),
    ("Ishraqat Festival", "هوية أكبر مهرجان فني وثقافي تشهده سوريا في الذاكرة الحديثة، أُقيم على مسرح دار الأوبرا بدمشق. وقد كُرِّم هذا العمل على ذات المسرح."),
    ("is it", "هوية لشركة متخصصة في الذكاء الاصطناعي (AI) والحلول التقنية، تُحوّل سؤالًا بسيطًا إلى تصريح."),
    ("Najd", "علامة تجارية لمصنّع فواصل الألمنيوم، متجذرة في التراث النجدي ومبنية على القوة والدقة، من الشعار إلى وسائل التواصل الاجتماعي."),
    ("Moments", "شعار، ودليل هوية، ووسائل تواصل اجتماعي لعلامة تنظيم فعاليات من pausa، تركّز على احتفالات الأطفال واللحظات الجديرة بالحفظ."),
    ("Syrian Airlines", "ناقل وطني أُعيد بناؤه من الصفر: شعار جديد، ونظام هوية متكامل، وأزياء موحّدة، وكل نقطة تماس بينهما."),
    ("Path@", "اسم وهوية لمبادرة تابعة لهيئة الترفيه العامة تربط المواهب الشابة بالمحترفين في مجالاتهم."),
    ("Allurium", "تمت تسميتها وبناؤها من الصفر لمصنّع فواصل ألمنيوم فاخرة: أنيقة، وقوية، ومهندسة لتبدو كذلك."),
]

def _cs_case_items_ar():
    items = []
    for name, desc in _CS_CASES_AR:
        items.append(("h3", name))
        items.append(("p", desc))
    return items

def creative_studio_ar_items():
    items = [
        ("p", "dot. creative studio، الرياض"),
        ("h1", "هوية العلامة التجارية والحملات التي تُنهي كل قاعدة بنقطة"),
        ("p", "نبني علامات تجارية لأصحاب الأعمال الذين سئموا اللعب بأمان. استراتيجية، وهوية، وحملات لا يمكنك تجاوزها بتمرير الشاشة."),
        ("p", "نحن استوديو للهوية التجارية والحملات الإبداعية مقرّه الرياض، المملكة العربية السعودية — استراتيجية، وتسمية، وهوية بصرية، وإعلان لشركات تريد أن تُذكر، لا أن تُرى فقط."),
        ("p", "استمر بالتمرير. نتحداك."),
        ("p", "أصبح التسويق مهذبًا. متوقعًا. آمنًا. وتلك هي الجريمة الحقيقية. لذا نكسر الطريقة المعتادة في العمل، علامة تجارية جريئة واحدة في كل مرة."),
        ("h2", "الأشياء الكبيرة تبدأ صغيرة"),
        ("p", "شعارنا يبدو كنقطة بسيطة. لا تدع ذلك يخدعك. كل علامة تجارية في هذه الملفات بدأت كفكرة صغيرة، ثم أصبح من المستحيل تجاهلها."),
        ("h2", "ملفات الأعمال"),
        ("p", "عشرون علامة تجارية توقفت عن اللعب بأمان. اضغط على أي ملف لرؤية العمل، ثم افتح الدراسة الكاملة على Behance."),
    ]
    items += _cs_case_items_ar()
    items += [
        ("h3", "المزيد على Behance"),
        ("p", "كنا سنعرض عليك كل أعمالنا هنا، لكن هذه الصفحة لا تدعم التمرير اللانهائي (بعد)."),
        ("h2", "الترسانة"),
        ("p", "ثلاث طرق للوصول إلى الناس. معظم العلامات التجارية تحتاج الثلاث تعمل معًا كواحدة."),
        ("p", "الوصول الجماهيري. العمل الذي تراه مدينة بأكملها."),
        ("p", "ظهر في: ملصقات شوارع مهرجان إشراقات، وشاشات مطارات الخطوط السورية."),
        ("li", "حملات إعلانات خارجية ولوحات طرق"),
        ("li", "المطبوعات والصحافة"),
        ("li", "شراء الوسائل الإعلامية والإعلانات المدفوعة"),
        ("li", "إنتاج الفيديو والموشن جرافيك"),
        ("p", "مباشر وملموس. العمل الذي يلمسه الناس ويزورونه ويشاركونه."),
        ("p", "ظهر في: أجنحة معارض الدهيان والسيف، وفعاليات Moments."),
        ("li", "أجنحة المعارض والفعاليات التنشيطية"),
        ("li", "الفعاليات والتجارب الحية"),
        ("li", "التسويق عبر المؤثرين"),
        ("li", "إدارة وسائل التواصل الاجتماعي"),
        ("li", "المنتجات الترويجية ومواد العلامة التجارية"),
        ("p", "كل شيء مترابط. فكرة واحدة تُحمل عبر كل قناة."),
        ("p", "ظهر في: Omnisphere، ونجد، والخطوط السورية، وPath@."),
        ("li", "استراتيجية العلامة التجارية وتموضعها"),
        ("li", "الهوية البصرية وإعادة العلامة التجارية"),
        ("li", "دليل الهوية وصوت العلامة التجارية"),
        ("li", "استراتيجية المحتوى وكتابة النصوص الإعلانية"),
        ("li", "تحسين محركات البحث (SEO) والمواقع الإلكترونية"),
        ("li", "الإخراج الإبداعي"),
        ("h2", "سلّم نفسك"),
        ("p", "هل لديك علامة تجارية تلعب بأمان زائد؟ أخبرنا عنها. كل رسالة تصل مباشرة إلى الفريق."),
    ]
    items += _cs_case_items_ar()
    return items

def load_sections():
    s = open(SRC, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'<script type="application/json" id="src-(\w+)">(.*?)</script>', s, re.S):
        out[m.group(1)] = json.loads(m.group(2))
    return out

def clean_text(txt):
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(txt)
    return re.sub(r"\s+", " ", txt).strip()

def strip_balanced_spans(h, opening_re):
    """Remove every <span ...> matched by `opening_re` together with its
    real matching closing tag, tracking nested <span>/</span> depth rather
    than stopping at the first </span> — some of these spans wrap an inline
    <span class="it">...</span> partway through, which a naive non-greedy
    regex cuts short, leaking the tail of that sentence as stray text."""
    out = []
    i = 0
    for m in re.finditer(opening_re, h):
        if m.start() < i:
            continue  # inside a span already removed
        out.append(h[i:m.start()])
        depth = 1
        pos = m.end()
        for tm in re.finditer(r"<span\b[^>]*>|</span>", h[pos:]):
            depth += 1 if tm.group(0) != "</span>" else -1
            if depth == 0:
                i = pos + tm.end()
                break
        else:
            i = len(h)  # unbalanced — drop to end rather than corrupt further
    out.append(h[i:])
    return "".join(out)

def clean_en(h):
    """Strip scripts/styles and drop the Arabic half of any en/ar span pair."""
    h = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    h = strip_balanced_spans(h, r'<span[^>]*lang="ar"[^>]*>')
    return h

def clean_ar_spans(h):
    """The inverse of clean_en, for brands (creative-consultancy) that store
    both languages as sibling spans in the same markup: drop the English half."""
    h = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    h = strip_balanced_spans(h, r'<span class="en">')
    return h

def extract(h):
    """Pull headings/paragraphs/list items in document order as (tag, text)."""
    items = []
    for m in re.finditer(r"<(h1|h2|h3|p|li)\b[^>]*>(.*?)</\1>", h, re.S):
        txt = clean_text(m.group(2))
        if txt and len(txt) > 1:
            items.append((m.group(1), txt))
    return items

def extract_i18n_ar(h, ar_dict):
    """For brands whose real bilingual system is data-i18n="key" attributes
    plus a separate Arabic string dictionary: walk the same elements in the
    same document order as the English page, and substitute each one's real
    Arabic string from that dictionary. Elements with no matching key (menus,
    decorative bits) are skipped rather than guessed at."""
    items = []
    for m in re.finditer(r'<(h1|h2|h3|p|li)\b[^>]*\bdata-i18n="([\w.]+)"[^>]*>', h):
        tag, key = m.group(1), m.group(2)
        if key in ar_dict:
            txt = clean_text(ar_dict[key])
            if txt and len(txt) > 1:
                items.append((tag, txt))
    return items

def to_semantic_html(items):
    """Render the extracted (tag,text) stream as clean nested HTML, grouping
    list items into <ul> and demoting the page's own h1 to a lead paragraph
    (the static page supplies its own h1)."""
    out, in_list, first_h1_seen = [], False, False
    for tag, txt in items:
        if tag == "li":
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{html.escape(txt)}</li>")
            continue
        if in_list:
            out.append("</ul>"); in_list = False
        if tag == "h1":
            out.append(f"<p class=\"lead\">{html.escape(txt)}</p>" if not first_h1_seen else f"<h2>{html.escape(txt)}</h2>")
            first_h1_seen = True
            continue
        out.append(f"<{tag}>{html.escape(txt)}</{tag}>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)

def faq_pairs(items):
    """Pick heading/paragraph pairs that already read like a question and
    answer (Latin or Arabic question mark), for FAQPage structured data —
    purely mechanical, only text that already exists on the page."""
    pairs = []
    for i, (tag, txt) in enumerate(items):
        if tag in ("h2", "h3") and txt.strip().endswith(("?", "؟")) and len(txt) < 140:
            for j in range(i + 1, min(i + 4, len(items))):
                if items[j][0] == "p":
                    pairs.append((txt, items[j][1]))
                    break
    return pairs[:8]

def parse_js_object(h, marker):
    """Pull a `const NAME = { ... }` JS object literal out of a larger JS
    blob and parse it: balance braces to find the real end (ignores nesting
    depth from [] since only {} are counted), quote bare identifier keys so
    it becomes valid JSON, and drop trailing commas."""
    start = h.index(marker)
    b0 = h.index("{", start)
    depth = 0
    for idx in range(b0, len(h)):
        if h[idx] == "{":
            depth += 1
        elif h[idx] == "}":
            depth -= 1
            if depth == 0:
                b1 = idx + 1
                break
    block = h[b0:b1]
    block = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_.]*)\s*:', r'\1"\2":', block)
    block = re.sub(r',\s*([}\]])', r'\1', block)
    return json.loads(block)

def extract_balanced_array(h, key):
    k = h.index(f'"{key}":')
    start = h.index("[", k)
    depth = 0
    for idx in range(start, len(h)):
        if h[idx] == "[":
            depth += 1
        elif h[idx] == "]":
            depth -= 1
            if depth == 0:
                return json.loads(h[start:idx + 1])
    raise ValueError(f"unbalanced array for {key}")

HREFLANG_TMPL = (
    '<link rel="alternate" hreflang="en" href="{en}">\n'
    '<link rel="alternate" hreflang="ar" href="{ar}">\n'
    '<link rel="alternate" hreflang="x-default" href="{en}">'
)

PAGE_TMPL = """<!doctype html>
<html lang="{lang}" dir="{dir}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow">
{hreflang}
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-5KTNW8VJXT"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-5KTNW8VJXT');
</script>
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
.kicker{{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);margin:-4px 0 8px}}
h2{{font-size:22px;margin:40px 0 10px}}
h3{{font-size:17px;margin:20px 0 6px}}
p{{margin:0 0 14px}}
ul{{margin:0 0 18px;padding-inline-start:22px}}
li{{margin:0 0 8px}}
.cta{{display:inline-block;margin:36px 0 8px;padding:14px 26px;background:var(--accent);color:var(--on);text-decoration:none;font-weight:700;border-radius:8px}}
.foot{{margin-top:56px;padding-top:20px;border-top:1px solid var(--line);color:var(--mut);font-size:13px}}
.foot a{{color:var(--mut)}}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
<a class="brand" href="{home}">dot<b>.</b></a>
<nav class="crumbs"><a href="{home}">dot.</a> / {name}</nav>
</header>
<main>
<h1>{h1}</h1>
{body}
<a class="cta" href="{domain}/#{hash}">{cta}</a>
</main>
<div class="foot">
<p>{name}, {tagline}. <a href="mailto:info@dot-cs.com">info@dot-cs.com</a></p>
<p>{footlinks}</p>
</div>
</div>
</body>
</html>
"""

def page_urls(paths):
    """paths: dict slug -> {'en': url_or_None, 'ar': url_or_None}"""
    return paths

def render_page(*, lang, title, desc, url, color, on, name, h1, body, hash_, schema_blocks,
                 home_url, foot_links, en_url=None, ar_url=None):
    dir_ = "rtl" if lang == "ar" else "ltr"
    cta = "افتح الموقع التفاعلي الكامل &larr;" if lang == "ar" else "Open the full interactive site &rarr;"
    tagline = "جزء من dot. — الرياض، المملكة العربية السعودية" if lang == "ar" else "part of dot. &mdash; Riyadh, Saudi Arabia"
    hreflang = HREFLANG_TMPL.format(en=en_url, ar=ar_url) if (en_url and ar_url) else ""
    schema = "\n".join(
        f'<script type="application/ld+json">{json.dumps(sb, ensure_ascii=False)}</script>' for sb in schema_blocks
    )
    return PAGE_TMPL.format(
        lang=lang, dir=dir_, title=html.escape(title), desc=html.escape(desc), url=url,
        hreflang=hreflang, schema=schema, color=color, on=on, home=home_url,
        name=html.escape(name), h1=html.escape(h1), body=body, domain=DOMAIN, hash=hash_,
        cta=cta, tagline=tagline, footlinks=foot_links,
    )

CASE_STUDY_PATH = "tech-studio-results"

def foot_links_for(lang, current_path):
    """Cross-links to the other pages, in the same language where a
    translation exists, falling back to the English page (labelled) where
    it doesn't."""
    home = f'{DOMAIN}/' if lang == "en" else f'{DOMAIN}/ar/'
    entries = [
        ("home", "dot. home" if lang == "en" else "الرئيسية", home),
        ("creative-studio", "creative studio", f"{DOMAIN}/{'ar/' if lang=='ar' else ''}creative-studio/"),
        ("tech-studio", "tech studio", f"{DOMAIN}/{'ar/' if lang=='ar' else ''}tech-studio/"),
        ("tech-studio-profile", "tech studio profile", f"{DOMAIN}/{'ar/' if lang=='ar' else ''}tech-studio-profile/"),
        ("tech-studio-results", "client results", f"{DOMAIN}/{'ar/' if lang=='ar' else ''}tech-studio-results/"),
        ("creative-consultancy", "creative consultancy", f"{DOMAIN}/{'ar/' if lang=='ar' else ''}creative-consultancy/"),
    ]
    parts = [f'<a href="{u}">{html.escape(t)}</a>' for _, t, u in entries]
    return " &middot; ".join(parts)

DOOR_PANELS = ["creative-studio", "tech-studio", "creative-consultancy"]  # the shell's own 3 buttons

def build_ar_home_page(sections, raw_shell):
    """The front-door shell itself (public/index.html) turns out to have no
    Arabic content at all — its button labels are English-only, unlike the
    three sub-sites it links to. So this isn't a case of untangling mixed
    languages at one URL (like the sub-sites were); it's building a real
    Arabic entry point that didn't exist, reusing the real Arabic sentences
    already sourced from each sub-site wherever one exists."""
    panel_re = re.compile(r'<button type="button" class="panel p-\w+" data-site="([\w-]+)" aria-label="([^"]+)"')
    en_taglines = dict(panel_re.findall(raw_shell))

    ar_dict_tech = parse_js_object(sections["tech"], "const AR = {")
    ar_dict_profile = parse_js_object(sections["profile"], "const AR = {")
    cc_ar_items = extract(clean_ar_spans(sections["cc"]))
    cc_lead = next((t for tag, t in cc_ar_items if tag == "p"), None)
    # (not "first p" like cc_lead below — that would grab the location kicker
    # line rather than the actual descriptive sentence)
    cs_lead = "نبني علامات تجارية لأصحاب الأعمال الذين سئموا اللعب بأمان. استراتيجية، وهوية، وحملات لا يمكنك تجاوزها بتمرير الشاشة."

    # slug -> (arabic tagline or None, target url)
    entries = [
        ("creative-studio", cs_lead, f"{DOMAIN}/ar/creative-studio/", "dot. creative studio"),
        ("tech-studio", clean_text(ar_dict_tech.get("hero.lead", "")), f"{DOMAIN}/ar/tech-studio/", "dot. tech studio"),
        ("creative-consultancy", cc_lead, f"{DOMAIN}/ar/creative-consultancy/", "dot. creative consultancy"),
    ]
    secondary = [
        ("tech-studio-profile", clean_text(ar_dict_profile.get("about.lead", "")), f"{DOMAIN}/ar/tech-studio-profile/", "dot. tech studio — الملف التعريفي"),
        ("tech-studio-results", None, f"{DOMAIN}/ar/{CASE_STUDY_PATH}/", "dot. tech studio — نتائج العملاء"),
    ]

    title = "dot. | ستوديو إبداعي وستوديو تقني واستشارات إبداعية"
    desc = ("دوت. في الرياض: ستوديو إبداعي للعلامات التجارية، وستوديو تقني للذكاء الاصطناعي وأنظمة الأعمال، "
            "واستشارات إبداعية تُصلح الشركة وتروي قصتها.")
    h1 = "دوت. لديها ثلاثة مواقع. اختر واحدًا."

    parts = [f'<p class="lead">{html.escape(desc)}</p>']
    for slug, ar_line, url, label in entries:
        parts.append(f'<h2><a href="{url}">{html.escape(label)}</a></h2>')
        if ar_line:
            parts.append(f"<p>{html.escape(ar_line)}</p>")
    parts.append("<h2>المزيد</h2><ul>")
    for slug, ar_line, url, label in secondary:
        parts.append(f'<li><a href="{url}">{html.escape(label)}</a></li>')
    parts.append("</ul>")
    body = "\n".join(parts)

    schema_blocks = [{
        "@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc,
        "url": f"{DOMAIN}/ar/", "isPartOf": {"@type": "WebSite", "name": "dot.", "url": DOMAIN},
        "about": {"@type": "Organization", "name": "dot."}, "inLanguage": "ar",
    }]
    page = render_page(
        lang="ar", title=title, desc=desc, url=f"{DOMAIN}/ar/", color="#0068FF", on="#FFFFFF",
        name="dot.", h1=h1, body=body, hash_="", schema_blocks=schema_blocks,
        home_url=f"{DOMAIN}/ar/", foot_links=foot_links_for("ar", ""),
        en_url=f"{DOMAIN}/", ar_url=f"{DOMAIN}/ar/",
    )
    # This page's own CTA should point at the real interactive front door,
    # not at a specific brand's hash — override the generic one.
    page = page.replace(
        f'<a class="cta" href="{DOMAIN}/#">{("افتح الموقع التفاعلي الكامل &larr;")}</a>',
        f'<a class="cta" href="{DOMAIN}/">افتح الموقع التفاعلي الكامل &larr;</a>',
    )
    outdir = os.path.join(ROOT, "public", "ar")
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
    print(f"wrote public/ar/index.html ({len(page)} bytes)")
    return f"{DOMAIN}/ar/"

def build():
    sections = load_sections()
    raw_shell = open(SRC, encoding="utf-8").read()
    en_urls, ar_urls = [], []
    ar_urls.append(build_ar_home_page(sections, raw_shell))

    # ---- tech-studio's bilingual client-results data (shared by that page
    #      and by the tech-studio / tech-profile "see all" link) ----
    data_obj = parse_js_object(sections["tech"], "const DATA = {")
    cases_en, cases_ar = data_obj["en"]["CASES"], data_obj["ar"]["CASES"]

    def case_studies_body(cases, lang):
        result_label = "النتيجة:" if lang == "ar" else "Result:"
        intro = (
            "سبعة عشر مشروعًا من أعمال dot. tech studio الفعلية مع عملائها في السعودية. "
            "أسماء العملاء غير مذكورة؛ القطاع والمشكلة والنتيجة المقاسة حقيقية."
            if lang == "ar" else
            "Seventeen engagements from dot. tech studio's own client work in Saudi Arabia. "
            "Client names are withheld; the industry, the problem and the measured result are real."
        )
        parts = [f'<p class="lead">{intro}</p>']
        schema_items = []
        for i, c in enumerate(cases, 1):
            name = f"{c['ind']}: {c['t']}"
            parts.append(f'<h2 id="case-{i}">{html.escape(name)}</h2>')
            parts.append(f'<p class="kicker">{html.escape(c["ind"])}</p>')
            parts.append(f'<p>{html.escape(c["body"])}</p>')
            parts.append(f'<p><b>{result_label}</b> {html.escape(c["fig"])}</p>')
            schema_items.append({"@type": "Article", "headline": name, "articleSection": c["ind"],
                                  "abstract": c["body"], "about": c["fig"]})
        return "\n".join(parts), schema_items

    for lang, cases in (("en", cases_en), ("ar", cases_ar)):
        path_prefix = "" if lang == "en" else "ar/"
        url = f"{DOMAIN}/{path_prefix}{CASE_STUDY_PATH}/"
        body, schema_items = case_studies_body(cases, lang)
        title = ("Client results | dot. tech studio, Saudi Arabia" if lang == "en"
                  else "نتائج العملاء | dot. tech studio، السعودية")
        desc = ("Seventeen real engagements for insurance, payments, healthcare and manufacturing "
                "companies in Saudi Arabia, anonymised by industry, with the numbers behind each one."
                if lang == "en" else
                "سبعة عشر مشروعًا حقيقيًا لشركات تأمين ومدفوعات ورعاية صحية وتصنيع في السعودية، "
                "دون ذكر أسماء العملاء، مع الأرقام الفعلية لكل مشروع.")
        h1 = "Client results, by the numbers" if lang == "en" else "نتائج العملاء، بالأرقام"
        schema_blocks = [{
            "@context": "https://schema.org", "@type": "CollectionPage", "name": title,
            "description": desc, "url": url, "isPartOf": {"@type": "WebSite", "name": "dot.", "url": DOMAIN},
            "about": {"@type": "Organization", "name": "dot. tech studio"}, "hasPart": schema_items,
        }]
        page = render_page(
            lang=lang, title=title, desc=desc, url=url, color="#00F4C9", on="#121D21",
            name="dot. tech studio", h1=h1, body=body, hash_="tech-studio", schema_blocks=schema_blocks,
            home_url=f"{DOMAIN}/" if lang == "en" else f"{DOMAIN}/ar/",
            foot_links=foot_links_for(lang, CASE_STUDY_PATH),
            en_url=f"{DOMAIN}/{CASE_STUDY_PATH}/", ar_url=f"{DOMAIN}/ar/{CASE_STUDY_PATH}/",
        )
        outdir = os.path.join(ROOT, "public", path_prefix, CASE_STUDY_PATH)
        os.makedirs(outdir, exist_ok=True)
        open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
        (en_urls if lang == "en" else ar_urls).append(url)
        print(f"wrote public/{path_prefix}{CASE_STUDY_PATH}/index.html ({len(page)} bytes, {len(cases)} cases, {lang})")

    see_results_link = {
        "en": f'\n<p><a href="{DOMAIN}/{CASE_STUDY_PATH}/">See all 17 client results, by the numbers &rarr;</a></p>',
        "ar": f'\n<p><a href="{DOMAIN}/ar/{CASE_STUDY_PATH}/">اطّلع على نتائج العملاء السبعة عشر بالأرقام &larr;</a></p>',
    }

    # ---- the four brand pages ----
    for slug, b in BRANDS.items():
        raw = sections[b["key"]]
        en_url = f"{DOMAIN}/{b['path']}/"
        ar_url = f"{DOMAIN}/ar/{b['path']}/" if b["i18n"] else None

        # English (always built the same way, regardless of i18n system)
        items = extract(clean_en(raw))
        h1 = next((t for tag, t in items if tag == "h1"), b["name"])
        body = to_semantic_html(items)
        faqs = faq_pairs(items) + MANUAL_FAQS.get(slug, [])
        faq_html = "\n".join(f"<h3>{html.escape(q)}</h3>\n<p>{html.escape(a)}</p>" for q, a in MANUAL_FAQS.get(slug, []))
        if faq_html:
            body += f"\n<h2>Pricing</h2>\n{faq_html}"
        if slug in ("tech-studio", "tech-profile"):
            body += see_results_link["en"]
        schema_blocks = [{
            "@context": "https://schema.org", "@type": "WebPage", "name": b["title"], "description": b["desc"],
            "url": en_url, "isPartOf": {"@type": "WebSite", "name": "dot.", "url": DOMAIN},
            "about": {"@type": "Organization", "name": b["name"]},
        }]
        if faqs:
            schema_blocks.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]})
        page = render_page(
            lang="en", title=b["title"], desc=b["desc"], url=en_url, color=b["color"], on=b["on"],
            name=b["name"], h1=h1, body=body, hash_=slug, schema_blocks=schema_blocks,
            home_url=f"{DOMAIN}/", foot_links=foot_links_for("en", b["path"]),
            en_url=en_url, ar_url=ar_url,
        )
        outdir = os.path.join(ROOT, "public", b["path"])
        os.makedirs(outdir, exist_ok=True)
        open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
        en_urls.append(en_url)
        print(f"wrote public/{b['path']}/index.html ({len(page)} bytes, {len(faqs)} FAQ pairs, en)")

        # Arabic counterpart, only where the source actually has one
        if not b["i18n"]:
            continue
        if b["i18n"] == "dict":
            ar_dict = parse_js_object(raw, "const AR = {")
            ar_items = extract_i18n_ar(raw, ar_dict)
            ar_title = ar_dict.get("__title", b["title"])
            ar_desc = None
        elif b["i18n"] == "manual":
            ar_dict = None
            ar_items = creative_studio_ar_items()
            ar_title = CREATIVE_STUDIO_AR_TITLE
            ar_desc = CREATIVE_STUDIO_AR_DESC
        else:  # "spans"
            ar_dict = None
            ar_items = extract(clean_ar_spans(raw))
            ar_title_match = re.search(r"\|\s*([^<]+)$", b["title"])
            ar_title = f'{ar_title_match.group(1).strip()} | {b["name"]}' if ar_title_match else b["title"]
            ar_desc = None
        ar_h1 = next((t for tag, t in ar_items if tag == "h1"), b["name"])
        ar_body = to_semantic_html(ar_items)
        ar_faqs = faq_pairs(ar_items) + MANUAL_FAQS_AR.get(slug, [])
        ar_faq_html = "\n".join(f"<h3>{html.escape(q)}</h3>\n<p>{html.escape(a)}</p>" for q, a in MANUAL_FAQS_AR.get(slug, []))
        if ar_faq_html:
            ar_body += f"\n<h2>الأسعار</h2>\n{ar_faq_html}"
        if slug in ("tech-studio", "tech-profile"):
            ar_body += see_results_link["ar"]
        if ar_desc is None:
            # A short, honestly-derived Arabic meta description: the first real
            # translated lead paragraph, not a fresh composition.
            ar_lead = next((t for tag, t in ar_items if tag in ("h1", "p")), ar_h1)
            ar_desc = (ar_lead[:157] + "…") if len(ar_lead) > 158 else ar_lead
        ar_schema_blocks = [{
            "@context": "https://schema.org", "@type": "WebPage", "name": ar_title, "description": ar_desc,
            "url": ar_url, "isPartOf": {"@type": "WebSite", "name": "dot.", "url": DOMAIN},
            "about": {"@type": "Organization", "name": b["name"]}, "inLanguage": "ar",
        }]
        if ar_faqs:
            ar_schema_blocks.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in ar_faqs]})
        ar_page = render_page(
            lang="ar", title=ar_title, desc=ar_desc, url=ar_url, color=b["color"], on=b["on"],
            name=b["name"], h1=ar_h1, body=ar_body, hash_=slug, schema_blocks=ar_schema_blocks,
            home_url=f"{DOMAIN}/ar/", foot_links=foot_links_for("ar", b["path"]),
            en_url=en_url, ar_url=ar_url,
        )
        ar_outdir = os.path.join(ROOT, "public", "ar", b["path"])
        os.makedirs(ar_outdir, exist_ok=True)
        open(os.path.join(ar_outdir, "index.html"), "w", encoding="utf-8").write(ar_page)
        ar_urls.append(ar_url)
        print(f"wrote public/ar/{b['path']}/index.html ({len(ar_page)} bytes, {len(ar_faqs)} FAQ pairs, ar)")

    # sitemap.xml
    today = datetime.date.today().isoformat()
    all_urls = [f"{DOMAIN}/"] + en_urls + ar_urls
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in all_urls:
        sm.append(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "public", "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    print("wrote public/sitemap.xml")

    # robots.txt
    open(os.path.join(ROOT, "public", "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n"
    )
    print("wrote public/robots.txt")

    # llms.txt — AEO: a plain-language summary for AI assistants / answer engines
    llms = f"""# dot.

> dot. is a Riyadh-based group of three businesses that work together: a creative studio, a tech studio, and a creative consultancy that combines both. It serves companies in Saudi Arabia. Most pages are available in English and Arabic.

## Businesses

- Arabic entry point: [{DOMAIN}/ar/]({DOMAIN}/ar/)
- [dot. creative studio]({DOMAIN}/creative-studio/) / [Arabic]({DOMAIN}/ar/creative-studio/): brand strategy, identity, and advertising campaigns.
- [dot. tech studio]({DOMAIN}/tech-studio/) / [Arabic]({DOMAIN}/ar/tech-studio/): AI and automation, business systems, data, and rescuing stalled technology projects, for regulated industries such as insurance and payments in Saudi Arabia.
- [dot. tech studio — company profile]({DOMAIN}/tech-studio-profile/) / [Arabic]({DOMAIN}/ar/tech-studio-profile/): the full company profile for dot. tech studio.
- [dot. tech studio — client results]({DOMAIN}/tech-studio-results/) / [Arabic]({DOMAIN}/ar/tech-studio-results/): seventeen real, anonymised engagements with the measured before/after numbers.
- [dot. creative consultancy]({DOMAIN}/creative-consultancy/) / [Arabic]({DOMAIN}/ar/creative-consultancy/): a business consultancy with creative solutions — finds what is holding a company back, fixes it, and builds the story to tell about it.

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
