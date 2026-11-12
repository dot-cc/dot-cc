"""Add an Arabic version (for people) to the creative studio site bundle: public/sites/studio.json.
Same pattern as the consultancy site: a language button, body[data-lang], html dir=rtl, Alexandria for Arabic,
the choice kept in localStorage "dotLang" (also set by /ar/creative-studio/) and ?lang=ar|en.
The English markup is untouched; a dictionary swaps text at runtime, so the scroll animations keep working.
Run from the dot-cc repo root, after add_lead_paths_studio.py. Idempotent."""
import json, re, sys

P = "public/sites/studio.json"
FONT = sys.argv[1] if len(sys.argv) > 1 else None   # optional file with the @font-face rule; default: read it from sites/cc.json

raw = open(P).read()
s = json.loads(raw)
def enc(x): return json.dumps(x).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
assert enc(s) == raw
if "/* arabic:start */" in s:
    print("already has Arabic"); sys.exit(0)

def once(old, new):
    global s
    assert s.count(old) == 1, ("not unique", old[:60], s.count(old))
    s = s.replace(old, new)

AR = {
 # header and hero
 "Work": "أعمالنا", "Services": "خدماتنا", "Start a brief": "ابدأ مشروعك",
 "dot. creative studio, Riyadh": "استوديو dot. الإبداعي، الرياض",
 "Brand identity and campaigns that end every rule with a dot": "هويات وحملات تُنهي كل قاعدة بنقطة",
 "We build brands for people who are done playing it safe. Strategy, identity, and campaigns you can't scroll past.":
   "نبني علامات لمن سئم اللعب في المنطقة الآمنة. استراتيجية وهوية وحملات لا يمكن تجاوزها بالتمرير.",
 "We're a brand identity and creative campaign studio based in Riyadh, Saudi Arabia — strategy, naming, visual identity and advertising for companies that want to be remembered, not just seen.":
   "استوديو للهويات والحملات الإبداعية في الرياض، المملكة العربية السعودية: استراتيجية وتسمية وهوية بصرية وإعلان، للشركات التي تريد أن تُتذكَّر لا أن تُرى فقط.",
 "Book a 15-minute call": "احجز مكالمة 15 دقيقة",
 "Keep scrolling. We dare you.": "واصل التمرير. نتحدّاك.",
 # trusted by and names that have an Arabic name
 "Trusted by": "وثق بنا",
 "Syrian Airlines": "السورية للطيران",
 "General Entertainment Authority (Path@)": "الهيئة العامة للترفيه (Path@)",
 "Ishraqat Festival": "مهرجان إشراقات",
 # stamps and tapes
 "Say yes to": "نعم لـ", "Fresh, groundbreaking, fearless.": "الجديد والمبتكر والجريء.",
 "Say no to": "لا لـ", "Playing it safe and the same old routines.": "اللعب الآمن والروتين المعتاد.",
 "No rules": "بلا قواعد", "No boring brands": "لا علامات مملّة", "No playing it safe": "لا للعب الآمن",
 "Always leave a dot": "اترك نقطة دائمًا", "Fresh": "جديد", "Groundbreaking": "مبتكر", "Fearless": "جريء",
 "Big things start small": "الأشياء الكبيرة تبدأ صغيرة",
 "Our logo looks like a simple dot. Don't let that fool you. Every brand in these files started as one small idea, then got impossible to ignore.":
   "شعارنا يبدو نقطة بسيطة. لا تدع ذلك يخدعك. كل علامة في هذه الملفات بدأت بفكرة صغيرة واحدة، ثم صار تجاهلها مستحيلًا.",
 # cases
 "Case files": "ملفات القضايا",
 "Twenty brands that stopped playing it safe. Tap a file to see the work, then open the full case on Behance.":
   "عشرون علامة توقفت عن اللعب الآمن. افتح أي ملف لترى العمل، ثم شاهد القضية كاملة على Behance.",
 "Open the file": "افتح الملف",
 "Naming and brand system": "التسمية ونظام العلامة", "Multi-brand identity": "هوية متعددة العلامات",
 "Industrial rebrand": "إعادة هوية صناعية", "Food brand rebrand": "إعادة هوية لعلامة طعام",
 "Logistics identity": "هوية لوجستية", "Identity and product design": "هوية وتصميم منتجات",
 "Naming and identity": "التسمية والهوية", "Arts and culture": "فنون وثقافة", "Tech branding": "هوية تقنية",
 "Industrial identity": "هوية صناعية", "Events brand": "علامة فعاليات", "National airline rebrand": "إعادة هوية ناقل وطني",
 "With the General Entertainment Authority": "مع الهيئة العامة للترفيه",
 "Named and built from scratch. One star-guided brand system holding three businesses: production, construction, and consultancy.":
   "سمّيناها وبنيناها من الصفر. نظام علامة واحد تهديه النجوم ويجمع ثلاثة أعمال: الإنتاج والمقاولات والاستشارات.",
 "One family, three lines: luxury, cash and carry, and HORECA (hotels, restaurants, and cafes). Identity, social media, and exhibition booths.":
   "عائلة واحدة وثلاثة خطوط: الفاخر، والجملة، وقطاع الفنادق والمطاعم والمقاهي. هوية ووسائل تواصل اجتماعي وأجنحة معارض.",
 "A rebrand, exhibition booths, and campaigns sized for one of Saudi Arabia's leading aluminum cladding factories.":
   "إعادة هوية وأجنحة معارض وحملات على مقاس أحد أبرز مصانع ألواح الألمنيوم في المملكة العربية السعودية.",
 "A full rebrand for a Saudi cloud kitchen delivering premium meat. Culinary tradition meets fast delivery, across packaging and social media.":
   "إعادة هوية كاملة لمطبخ سحابي سعودي يوصّل اللحوم الفاخرة. أصالة الطهي تلتقي بسرعة التوصيل، من التغليف إلى وسائل التواصل الاجتماعي.",
 "An identity for a supply chain company that turns shipping and warehousing into a brand language about movement and reliability.":
   "هوية لشركة سلاسل إمداد تحوّل الشحن والتخزين إلى لغة علامة عن الحركة والموثوقية.",
 "A celestial identity for premium hospitality hollowware, plus silver pieces we sketched that are now in production and on fine-dining tables.":
   "هوية سماوية لأواني الضيافة الفاخرة، وقطع فضية رسمناها بأيدينا وهي اليوم في الإنتاج وعلى موائد المطاعم الراقية.",
 "Named and built from the first sketch: a hotel and restaurant supplies brand that carries the prestige its name promises.":
   "سمّيناها وبنيناها من أول رسمة: علامة لمستلزمات الفنادق والمطاعم تحمل الفخامة التي يعد بها اسمها.",
 "The identity for the largest arts and cultural festival Syria has seen in recent memory, staged at the Damascus Opera House. The work was honored on its stage.":
   "هوية أكبر مهرجان للفنون والثقافة شهدته سوريا منذ سنوات، على مسرح دار الأوبرا في دمشق. وكُرّم العمل على خشبته.",
 "An identity for an artificial intelligence (AI) and technical solutions company that turns a simple question into a statement.":
   "هوية لشركة ذكاء اصطناعي وحلول تقنية تحوّل سؤالًا بسيطًا إلى تصريح.",
 "A brand for an aluminum partition maker, rooted in Najdi heritage and built on strength and precision, from logo to social media.":
   "علامة لمصنع قواطع ألمنيوم، متجذرة في التراث النجدي ومبنية على القوة والدقة، من الشعار إلى وسائل التواصل الاجتماعي.",
 "Logo, guidelines, and social media for an events brand by pausa, focused on kids' celebrations and moments worth keeping.":
   "شعار ودليل هوية ووسائل تواصل اجتماعي لعلامة فعاليات من pausa، تركّز على احتفالات الأطفال واللحظات التي تستحق أن تبقى.",
 "A national carrier rebuilt from the ground up: new logo, full identity system, uniforms, and every touchpoint in between.":
   "ناقل وطني أُعيد بناؤه من الأساس: شعار جديد، ونظام هوية كامل، وأزياء موحدة، وكل نقطة تواصل بينها.",
 "Name and identity for a General Entertainment Authority initiative connecting young talent with professionals in their field.":
   "اسم وهوية لمبادرة من الهيئة العامة للترفيه تربط المواهب الشابة بالمحترفين في مجالاتهم.",
 "Named and built from scratch for a premium aluminum partitions maker: sleek, strong, and engineered to look it.":
   "سمّيناها وبنيناها من الصفر لمصنع قواطع ألمنيوم فاخرة: أنيقة وقوية ومصمَّمة لتبدو كذلك.",
 "More on Behance": "المزيد على Behance", "On Behance": "على Behance",
 "We'd show you all our work here, but this page doesn't support infinite scrolling (yet).":
   "كنا سنعرض كل أعمالنا هنا، لكن هذه الصفحة لا تدعم التمرير اللانهائي (حتى الآن).",
 "See everything on Behance": "شاهد كل أعمالنا على Behance",
 "See the full case on Behance": "شاهد القضية كاملة على Behance",
 "See more of our work on Behance": "شاهد المزيد من أعمالنا على Behance",
 # services
 "The arsenal": "الترسانة",
 "Three ways to reach people. Most brands need all three working as one.": "ثلاث طرق للوصول إلى الناس. ومعظم العلامات تحتاجها الثلاث معًا.",
 "Above the line": "فوق الخط", "Below the line": "تحت الخط", "Through the line": "عبر الخط",
 "Mass reach. The work a whole city sees.": "انتشار واسع. عمل تراه مدينة بأكملها.",
 "Direct and hands-on. The work people touch, visit, and share.": "مباشر وملموس. عمل يلمسه الناس ويزورونه ويشاركونه.",
 "Everything connected. One idea carried across every channel.": "كل شيء متصل. فكرة واحدة تمتد عبر كل قناة.",
 "Seen in: Ishraqat Festival street posters, Syrian Airlines airport screens.": "شاهدته في: ملصقات شوارع مهرجان إشراقات، وشاشات المطار للسورية للطيران.",
 "Seen in: Al Dahayan and Al Saif exhibition booths, Moments events.": "شاهدته في: أجنحة معارض Al Dahayan وAl Saif، وفعاليات Moments.",
 "Seen in: Omnisphere, Najd, Syrian Airlines, Path@.": "شاهدته في: Omnisphere وNajd والسورية للطيران وPath@.",
 "Outdoor and billboard campaigns": "حملات الطرق واللوحات الإعلانية", "Print and press": "المطبوعات والصحافة",
 "Media buying and paid ads": "شراء الوسائط والإعلانات المدفوعة", "Video and motion production": "إنتاج الفيديو والموشن جرافيك",
 "Exhibition booths and activations": "أجنحة المعارض والتفعيلات", "Events and experiential": "الفعاليات والتجارب",
 "Influencer marketing": "التسويق عبر المؤثرين", "Social media management": "إدارة وسائل التواصل الاجتماعي",
 "Merchandise and brand collateral": "الهدايا الترويجية ومطبوعات العلامة",
 "Brand strategy and positioning": "استراتيجية العلامة وتموضعها", "Visual identity and rebranding": "الهوية البصرية وإعادة الهوية",
 "Brand guidelines and voice": "دليل العلامة ونبرتها", "Content strategy and copywriting": "استراتيجية المحتوى وكتابة النصوص",
 "Search engine optimization (SEO) and web": "تحسين الظهور في محركات البحث والمواقع", "Creative direction": "الإدارة الإبداعية",
 # contact
 "Turn yourself": "سلّم", "in": "نفسك",
 "Got a brand that's playing it too safe? Tell us about it. Every message goes straight to the team.":
   "لديك علامة تلعب بأمان أكثر من اللازم؟ أخبرنا عنها. كل رسالة تصل إلى الفريق مباشرة.",
 "Not ready for a brief?": "لست جاهزًا لمشروع كامل؟",
 "Get a free brand check. Send us your logo and a few of your posts, and we reply with three fixes you can use straight away.":
   "احصل على فحص مجاني لعلامتك. أرسل لنا شعارك وبعض منشوراتك، ونرد عليك بثلاثة تحسينات تطبّقها فورًا.",
 "Get my free brand check": "أريد الفحص المجاني",
 "Your name": "اسمك", "Email": "البريد الإلكتروني", "Company (optional)": "الشركة (اختياري)",
 "What do you need?": "ماذا تحتاج؟", "A 15-minute call": "مكالمة 15 دقيقة", "Free brand check": "فحص مجاني للعلامة",
 "Brand identity": "هوية العلامة", "Campaign (ATL)": "حملة (فوق الخط)", "Activation or event (BTL)": "تفعيل أو فعالية (تحت الخط)",
 "Integrated campaign (TTL)": "حملة متكاملة (عبر الخط)", "Not sure yet": "لست متأكدًا بعد", "Tell us about it": "أخبرنا أكثر",
 "What are you building, and what's in the way?": "ماذا تبني، وما الذي يعترض طريقك؟",
 "Send to dot.": "أرسل إلى dot.",
 "Thanks. Your message has reached the team and we will come back to you soon.": "شكرًا. وصلت رسالتك إلى الفريق وسنعود إليك قريبًا.",
 "Your email app should open with the message ready to send. Nothing opened?": "سيفتح تطبيق البريد لديك والرسالة جاهزة للإرسال. لم يُفتح شيء؟",
 "Open it here": "افتحها من هنا", "or write to info@dot-cs.com.": "أو راسلنا على info@dot-cs.com.",
 "Add your name so we know who to call.": "أضف اسمك لنعرف بمن نتصل.",
 "Add an email we can reply to, like you@company.com.": "أضف بريدًا نستطيع الرد عليه، مثل you@company.com.",
 "Tell us a little about what you need.": "أخبرنا قليلًا عمّا تحتاجه.",
 # footer, modal, WhatsApp, labels
 "Creative studio. Riyadh, Saudi Arabia.": "استوديو إبداعي. الرياض، المملكة العربية السعودية.",
 "Always leave a dot.": "اترك نقطة دائمًا.", "© 2026 dot. creative studio": "© 2026 استوديو dot. الإبداعي",
 "Chat on WhatsApp": "تحدّث معنا على واتساب", "Chat with dot. on WhatsApp": "تحدّث مع dot. على واتساب",
 "Close": "إغلاق", "Previous image": "الصورة السابقة", "Next image": "الصورة التالية",
 "Introduction": "مقدمة", "Main": "القائمة الرئيسية", "What we believe": "ما نؤمن به", "Contact": "تواصل",
 "dot. creative studio, back to top": "استوديو dot. الإبداعي، إلى الأعلى", "dot. creative studio": "استوديو dot. الإبداعي",
}
# The manifesto keeps its 24 animated word slots; the Arabic fills them in order (slot 5 is the struck-through word).
MAN = ["التسويق", "صار", "مهذّبًا.", "متوقَّعًا.", "آمنًا.", "وهذه", "هي", "الجريمة", "الحقيقية.", "لذلك", "نكسر",
       "الطريقة", "المعتادة", "في", "العمل،", "علامة", "جريئة", "في", "كل", "مرة.", "", "", "", ""]

if FONT:
    font = open(FONT).read().strip()
else:
    _cc = json.loads(open("public/sites/cc.json").read())
    font = re.search(r'@font-face\{font-family:"Alexandria"[^}]*\}', _cc).group(0)
assert font.startswith('@font-face{font-family:"Alexandria"')

# float positions, mirrored for Arabic (they sit on the right in English)
mirror = []
for m in re.finditer(r'\.(f\d)\{([^}]*)\}', s):
    body = m.group(2)
    if 'right:' in body and 'left:' not in body:
        val = re.search(r'right:([^;}]+)', body).group(1)
        mirror.append('body[data-lang="ar"] .%s{right:auto;left:%s}' % (m.group(1), val))

css = """
/* arabic:start */
%s
body[data-lang="ar"] *{font-family:"Alexandria","AG Text",sans-serif!important;letter-spacing:0!important}
body[data-lang="ar"] h1,body[data-lang="ar"] h2,body[data-lang="ar"] h3,body[data-lang="ar"] .man-text,body[data-lang="ar"] .tape-track span,
body[data-lang="ar"] .cta,body[data-lang="ar"] .send,body[data-lang="ar"] .hero-ctas a,body[data-lang="ar"] .offer-box a,body[data-lang="ar"] .trusted b,
body[data-lang="ar"] .svc-name,body[data-lang="ar"] .be-btn,body[data-lang="ar"] .case-open,body[data-lang="ar"] .stamp b,body[data-lang="ar"] .wa-btn,
body[data-lang="ar"] .direct,body[data-lang="ar"] .foot-sign{font-weight:800!important}
body[data-lang="ar"] .hero h1{line-height:1.22;font-size:clamp(2.6rem,8.4vw,7.6rem)}
body[data-lang="ar"] h2{line-height:1.2}
body[data-lang="ar"] .man-text{line-height:1.35}
body[data-lang="ar"] .contact h2{line-height:1.15}
body[data-lang="ar"] .tapes,body[data-lang="ar"] .gal{direction:ltr}
body[data-lang="ar"] .tape-track span{text-transform:none}
.lang-btn{font-family:"Alexandria","AG Text",sans-serif;font-weight:700;border:2px solid var(--ink);border-radius:999px;padding:7px 14px;text-decoration:none}
body[data-lang="ar"] .lang-btn{font-family:"AG Text",sans-serif!important}
@media (max-width:760px){.nav a.lang-btn{display:inline-block;padding:6px 11px;font-size:.85rem}.nav{gap:10px}}
%s
/* arabic:end */
""" % (font, "\n".join(mirror))
once("/* lead-paths:end */", "/* lead-paths:end */" + css)

# the language button, in the nav before "Start a brief"
once('<a href="#contact" class="cta">Start a brief</a>',
     '<a href="#" class="lang-btn" id="langBtn" lang="ar">عربي</a>\n      <a href="#contact" class="cta">Start a brief</a>')

js = """<script>/* arabic */(function(){
var AR=%s, MAN=%s;
var body=document.body, root=document.documentElement, orig=new WeakMap(), attrs=['aria-label','placeholder','title'];
var WA_EN='Hi dot. creative studio, I would like to talk about my brand.', WA_AR='مرحبًا dot.، أودّ التحدث عن علامتي.';
var PRE_EN='Free brand check, please. Our brand: ', PRE_AR='أريد فحصًا مجانيًا للعلامة. علامتنا: ';
function tr(t){var k=t.trim(); if(AR[k]) return t.replace(k,AR[k]);
  var m=k.match(/^File (\\d+) of (\\d+)$/); if(m) return t.replace(k,'الملف '+m[1]+' من '+m[2]);
  m=k.match(/^File (\\d+)$/); if(m) return t.replace(k,'ملف '+m[1]); return null;}
function walk(lang){
  var w=document.createTreeWalker(body,NodeFilter.SHOW_TEXT,{acceptNode:function(n){var p=n.parentNode&&n.parentNode.nodeName;
    return (p==='SCRIPT'||p==='STYLE')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}}),n;
  while((n=w.nextNode())){
    if(n.parentNode.closest&&n.parentNode.closest('.man-text'))continue;
    if(lang==='ar'){var t=orig.has(n)?orig.get(n):n.nodeValue, a=tr(t); if(a!==null){orig.set(n,t); n.nodeValue=a;}}
    else if(orig.has(n)){n.nodeValue=orig.get(n);}
  }
  body.querySelectorAll('['+attrs.join('],[')+']').forEach(function(el){attrs.forEach(function(a){
    var v=el.getAttribute(a); if(v===null)return; var key='data-en-'+a;
    if(lang==='ar'){var e=el.getAttribute(key)||v, x=tr(e); if(x!==null){el.setAttribute(key,e); el.setAttribute(a,x);}}
    else if(el.hasAttribute(key)){el.setAttribute(a,el.getAttribute(key));}
  });});
  document.querySelectorAll('.man-text .w').forEach(function(w,i){
    if(!w.hasAttribute('data-en'))w.setAttribute('data-en',w.textContent);
    w.textContent=lang==='ar'?(MAN[i]||''):w.getAttribute('data-en'); w.style.display=(lang==='ar'&&!MAN[i])?'none':'';});
  document.querySelectorAll('.wa-btn').forEach(function(a){a.href=a.href.replace(/text=.*$/,'text='+encodeURIComponent(lang==='ar'?WA_AR:WA_EN));});
  var m=document.querySelector('#briefForm textarea'); if(m){if(lang==='ar'&&m.value===PRE_EN)m.value=PRE_AR; if(lang==='en'&&m.value===PRE_AR)m.value=PRE_EN;}
}
var busy=false;
function setLang(l){busy=true; body.setAttribute('data-lang',l); root.setAttribute('lang',l); root.setAttribute('dir',l==='ar'?'rtl':'ltr');
  document.title=l==='ar'?'استوديو dot. الإبداعي':'dot. creative studio';
  var b=document.getElementById('langBtn'); if(b){b.textContent=l==='ar'?'English':'عربي'; b.setAttribute('lang',l==='ar'?'en':'ar');}
  walk(l); try{localStorage.setItem('dotLang',l);localStorage.setItem('dot-lang',l)}catch(e){} busy=false;}
var start='en'; try{var q=new URLSearchParams(location.search).get('lang'); try{q=q||new URLSearchParams(parent.location.search).get('lang')}catch(e){} var st=localStorage.getItem('dotLang');
  start=(q==='ar'||q==='en')?q:(st==='ar'||st==='en'?st:start);}catch(e){}
setLang(start);
var b=document.getElementById('langBtn'); if(b)b.addEventListener('click',function(ev){ev.preventDefault(); setLang(body.getAttribute('data-lang')==='ar'?'en':'ar');});
document.querySelectorAll('[data-check]').forEach(function(a){a.addEventListener('click',function(){
  var m=document.querySelector('#briefForm textarea'); if(m&&body.getAttribute('data-lang')==='ar'&&m.value===PRE_EN)m.value=PRE_AR;});});
var form=document.getElementById('briefForm');
if(form&&window.MutationObserver){new MutationObserver(function(){ if(busy||body.getAttribute('data-lang')!=='ar')return; busy=true; walk('ar'); busy=false;})
  .observe(form,{subtree:true,childList:true,characterData:true});}
})();</script>
""" % (json.dumps(AR, ensure_ascii=False), json.dumps(MAN, ensure_ascii=False))
once("</body>\n</html>", js + "</body>\n</html>")

open(P, "w").write(enc(s))
print("Arabic added:", len(AR), "strings,", len(mirror), "mirrored floats")
