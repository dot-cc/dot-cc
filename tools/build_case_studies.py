#!/usr/bin/env python3
"""Build one question-and-answer page per client result, in English and Arabic.

Source of truth is the same DATA.CASES object that feeds /tech-studio-results/
(read through build_static_pages.py), so every number and claim on these pages
is one already published there. The only text written here is the question
used as each page's title, plus the labels and links around the case text.

Writes public/case-studies/<slug>/index.html and public/ar/case-studies/<slug>/index.html,
updates sitemap.xml and llms.txt between marker comments, and adds a link from
each case on the results pages to its own page.

Run from anywhere:  python3 tools/build_case_studies.py
Uses the lead-form markup from build_static_pages.py, then adds the
post-submit redirect (_next) that the committed static pages carry.
"""
import html, importlib.util, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("bsp", os.path.join(HERE, "build_static_pages.py"))
bsp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bsp)

ROOT, DOMAIN = bsp.ROOT, bsp.DOMAIN
BASE = "case-studies"
TODAY = "2026-09-30"

# (slug, English question, Arabic question), in the same order as DATA.CASES.
QUESTIONS = [
    ("merge-three-insurance-databases",
     "Can three separate insurance databases be merged into one when the vendor says it is impossible?",
     "هل يمكن دمج ثلاث قواعد بيانات تأمين في مخطط واحد حين يعتبر المورّد ذلك مستحيلًا؟"),
    ("ten-years-of-claims-in-a-weekend",
     "How can ten years of insurance claims be uploaded to the regulator in one weekend?",
     "كيف تُرفع عشر سنوات من مطالبات التأمين إلى الجهة التنظيمية في عطلة نهاية أسبوع؟"),
    ("fix-insurance-oracle-integration",
     "How do you fix a faulty integration between an insurance core system and Oracle E-Business Suite?",
     "كيف يُصلح تكامل معيب بين نظام التأمين الأساسي وOracle E-Business Suite؟"),
    ("reconcile-300-million-sar",
     "How can a 300 million SAR mismatch between invoices and receipts be reconciled in seconds?",
     "كيف تُسوّى فروقات بين الفواتير والمقبوضات بقيمة 300 مليون ريال خلال ثوانٍ؟"),
    ("rescue-failing-budgeting-go-live",
     "Can a failing Hyperion budgeting go-live be rescued without an integration licence?",
     "هل يمكن إنقاذ إطلاق نظام موازنات متعثّر دون رخصة تكامل؟"),
    ("vendor-cannot-deliver-integrations",
     "What if a vendor cannot deliver enterprise integrations that were given three to six months?",
     "ماذا تفعل إذا عجز المورّد عن تسليم تكاملات مؤسسية مُنحت لها شهور؟"),
    ("migrate-legacy-insurance-system",
     "How do you migrate a legacy insurance system when the vendor will not give access?",
     "كيف تُرحَّل منظومة تأمين قديمة حين لا يمنحك المورّد إمكانية الوصول؟"),
    ("automate-motor-claims",
     "How do you automate motor claims with Najm and Yaqeen integrations?",
     "كيف تؤتمت مطالبات المركبات بالربط مع نجم ويقين؟"),
    ("speed-up-mass-policy-uploads",
     "Why are mass policy uploads slow, and how do you speed them up?",
     "لماذا يبطؤ الرفع الجماعي للوثائق، وكيف يُسرَّع؟"),
    ("claim-status-phone-line",
     "Can a self-service claim status phone line reduce call-centre load?",
     "هل يخفّف خط آلي للاستعلام عن المطالبات الضغط على مركز الاتصال؟"),
    ("rating-engine-rank-one",
     "How do you speed up an insurance rating engine so it ranks first on the SAMA price aggregator?",
     "كيف يُسرَّع محرّك تسعير التأمين ليتصدّر منصة مقارنة الأسعار في ساما؟"),
    ("motor-fraud-rules",
     "How do you detect motor insurance fraud with a rules-based process?",
     "كيف تُكشف حالات احتيال المركبات بقواعد منطقية؟"),
    ("find-factory-bottleneck",
     "How do you find the real bottleneck in a manufacturer with six factories?",
     "كيف تجد عنق الزجاجة الحقيقي في مصنع بستة مواقع؟"),
    ("payroll-report-18-hours-to-16-seconds",
     "How do you cut a payroll report for more than 10,000 employees from 18 hours to 16 seconds?",
     "كيف يُختصر تقرير رواتب لأكثر من 10,000 موظف من 18 ساعة إلى 16 ثانية؟"),
    ("upload-750000-policies-in-a-day",
     "How do you upload 750,000 motor policies in a single day?",
     "كيف تُرفع 750,000 وثيقة مركبات في يوم واحد؟"),
    ("independent-hospital-financial-audit",
     "Can an independent financial audit recover unbilled amounts at a hospital?",
     "هل يمكن للتدقيق المالي المستقل أن يسترد مبالغ غير مفوترة في مستشفى؟"),
    ("payments-licensing-architecture",
     "How does a payments company prepare its architecture for a SAMA technical audit and licence?",
     "كيف تُعدّ شركة مدفوعات بنيتها للتدقيق التقني لساما والترخيص؟"),
]

T = {
    "en": dict(short="The short answer", what="What the problem was and what was done", who="Industry",
               more="More client work", all="All 17 client results, by the numbers",
               studio="About dot. tech studio", contact="Talk to us",
               crumb="Client results", price="Engagements start at 3,750 SAR per month.",
               title_suffix="dot. tech studio, Saudi Arabia", cta="Open the full interactive site &rarr;",
               result_link="Read this as a question and answer &rarr;"),
    "ar": dict(short="الجواب المختصر", what="ما المشكلة وما الذي تم", who="القطاع",
               more="مزيد من أعمال العملاء", all="نتائج العملاء السبعة عشر بالأرقام",
               studio="عن dot. tech studio", contact="تواصل معنا",
               crumb="نتائج العملاء", price="تبدأ المشاريع من 3,750 ريال سعودي شهريًا.",
               title_suffix="dot. tech studio، السعودية", cta="افتح الموقع التفاعلي الكامل &larr;",
               result_link="اقرأها كسؤال وجواب &larr;"),
}


def load_cases():
    d = bsp.parse_js_object(bsp.load_sections()["tech"], "const DATA = {")
    en, ar = d["en"]["CASES"], d["ar"]["CASES"]
    assert len(en) == len(ar) == len(QUESTIONS), "question list out of sync with DATA.CASES"
    return en, ar


def with_redirect(form_html):
    """The committed static forms send people to /thanks/ after submit."""
    marker = '<input type="hidden" name="_captcha" value="false">'
    return form_html.replace(marker, marker + f'\n<input type="hidden" name="_next" value="{DOMAIN}/thanks/">', 1)


def build_page(lang, idx, case, other_case, slug, question, other_slug):
    t = T[lang]
    prefix = "" if lang == "en" else "ar/"
    url = f"{DOMAIN}/{prefix}{BASE}/{slug}/"
    en_url, ar_url = f"{DOMAIN}/{BASE}/{slug}/", f"{DOMAIN}/ar/{BASE}/{slug}/"
    results_url = f"{DOMAIN}/{prefix}tech-studio-results/"
    studio_url = f"{DOMAIN}/{prefix}tech-studio/"
    contact_url = f"{DOMAIN}/{prefix}contact/"
    answer_text = f"{case['fig']}"
    full_answer = f"{case['fig']} {case['body']}"

    # Related cases: the next three in the list, wrapping.
    related = []
    for k in range(1, 4):
        j = (idx + k) % len(QUESTIONS)
        related.append(j)
    rel_html = "\n".join(
        f'<li><a href="{DOMAIN}/{prefix}{BASE}/{QUESTIONS[j][0]}/">{html.escape(QUESTIONS[j][1 if lang == "en" else 2])}</a></li>'
        for j in related)

    body = "\n".join([
        f'<p class="kicker">{html.escape(t["who"])}: {html.escape(case["ind"])}</p>',
        f'<h2>{html.escape(t["short"])}</h2>',
        f'<p>{html.escape(case["fig"])}</p>',
        f'<h2>{html.escape(t["what"])}</h2>',
        f'<p>{html.escape(case["body"])}</p>',
        f'<p>{html.escape(t["price"])}</p>',
        f'<h2>{html.escape(t["more"])}</h2>',
        f'<ul>\n{rel_html}\n</ul>',
        f'<p><a href="{results_url}">{html.escape(t["all"])}</a> &middot; '
        f'<a href="{studio_url}">{html.escape(t["studio"])}</a> &middot; '
        f'<a href="{contact_url}">{html.escape(t["contact"])}</a></p>',
    ])
    body += "\n" + with_redirect(bsp.lead_form_html(lang, f"case-{slug}"[:60], "dot. tech studio"))

    title = f"{question} | {t['title_suffix']}"
    if lang == "en":
        desc = f"{case['fig']} A real dot. tech studio engagement, {case['ind'].lower()} sector, Saudi Arabia."
    else:
        desc = f"{case['fig']} مشروع حقيقي نفّذه dot. tech studio لعميل في قطاع {case['ind']} في السعودية."
    desc = desc[:300]

    schema = [
        {"@context": "https://schema.org", "@type": "WebPage", "name": question, "description": desc, "url": url,
         "inLanguage": lang, "isPartOf": {"@type": "WebSite", "name": "dot.", "url": DOMAIN},
         "about": {"@type": "Organization", "name": "dot. tech studio"}},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": question,
             "acceptedAnswer": {"@type": "Answer", "text": full_answer}}]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "dot.", "item": f"{DOMAIN}/{prefix}"},
            {"@type": "ListItem", "position": 2, "name": t["crumb"], "item": results_url},
            {"@type": "ListItem", "position": 3, "name": question, "item": url}]},
    ]
    page = bsp.render_page(
        lang=lang, title=title, desc=desc, url=url, color="#00F4C9", on="#121D21", name="dot. tech studio",
        h1=question, body=body, hash_="tech-studio", schema_blocks=schema,
        home_url=f"{DOMAIN}/{prefix}", foot_links=bsp.foot_links_for(lang, "tech-studio-results"),
        en_url=en_url, ar_url=ar_url)
    # Share image: tech studio card, not the group default.
    page = page.replace(f"{DOMAIN}/og/dot.png", f"{DOMAIN}/og/tech-studio.png")
    outdir = os.path.join(ROOT, "public", prefix, BASE, slug)
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
    return url


def update_results_pages(slugs):
    """Add a link under each case's Result line on the results pages (idempotent)."""
    for lang in ("en", "ar"):
        prefix = "" if lang == "en" else "ar/"
        p = os.path.join(ROOT, "public", prefix, "tech-studio-results", "index.html")
        h = open(p, encoding="utf-8").read()
        h = re.sub(r'<p class="case-link">.*?</p>\n?', "", h)
        label = T[lang]["result_link"]
        for i, slug in enumerate(slugs, 1):
            pat = re.compile(rf'(<h2 id="case-{i}">.*?</p>\s*<p><b>[^<]*</b>.*?</p>)', re.S)
            link = f'\n<p class="case-link"><a href="{DOMAIN}/{prefix}{BASE}/{slug}/">{label}</a></p>'
            h, n = pat.subn(lambda m: m.group(1) + link, h, count=1)
            assert n == 1, f"case {i} not found on {p}"
        open(p, "w", encoding="utf-8").write(h)


def update_sitemap_and_llms(slugs):
    p = os.path.join(ROOT, "public", "sitemap.xml")
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"  <!-- case-studies:start -->.*?  <!-- case-studies:end -->\n", "", s, flags=re.S)
    rows = ["  <!-- case-studies:start -->"]
    for prefix in ("", "ar/"):
        for slug in slugs:
            rows.append(f"  <url><loc>{DOMAIN}/{prefix}{BASE}/{slug}/</loc><lastmod>{TODAY}</lastmod></url>")
    rows.append("  <!-- case-studies:end -->")
    s = s.replace("</urlset>", "\n".join(rows) + "\n</urlset>")
    open(p, "w", encoding="utf-8").write(s)

    p = os.path.join(ROOT, "public", "llms.txt")
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"\n## Client work, one question per page\n.*?(?=\n## |\Z)", "", s, flags=re.S)
    block = ["\n## Client work, one question per page\n",
             "Each page answers one question with the measured result from a real dot. tech studio engagement (client names withheld). Arabic versions are under /ar/case-studies/.\n"]
    for slug, q, _ in QUESTIONS:
        block.append(f"- [{q}]({DOMAIN}/{BASE}/{slug}/)")
    s = s.replace("\n## Pricing", "\n".join(block) + "\n\n## Pricing", 1) if "\n## Pricing" in s else s + "\n".join(block) + "\n"
    open(p, "w", encoding="utf-8").write(s)


def main():
    en, ar = load_cases()
    slugs = [q[0] for q in QUESTIONS]
    for i, (slug, q_en, q_ar) in enumerate(QUESTIONS):
        build_page("en", i, en[i], ar[i], slug, q_en, slug)
        build_page("ar", i, ar[i], en[i], slug, q_ar, slug)
    update_results_pages(slugs)
    update_sitemap_and_llms(slugs)
    print(f"built {len(QUESTIONS)} questions x 2 languages = {2 * len(QUESTIONS)} pages")


if __name__ == "__main__":
    main()
