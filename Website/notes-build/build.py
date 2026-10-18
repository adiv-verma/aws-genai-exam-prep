# -*- coding: utf-8 -*-
"""Builds notes/concepts.html, notes/index.html and notes/map.html."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import DOMAINS, TASKS, GROUPS, CONCEPTS
import svgkit as K
from svgkit import DOM_COLOR, BOX_W, BOX_H, row_x, box, arrow, band_head, svg_open, svg_close, note, DIAGRAMS

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Website", "src", "notes")

ANCHOR = {t: ("t" if t == "4.2" else "s") for t in TASKS}  # 4.2 uses Topic anchors


def href(task, anc):
    return f"task-{task.replace('.', '-')}.html#{anc}"


def slug(name):
    s = re.sub(r"&[a-z]+;", " ", name).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


# --------------------------------------------------------------------------- #
#  Shared chrome
# --------------------------------------------------------------------------- #
BASE_CSS = """
  :root{
    --ink:#0b1524; --ink-soft:#3a4a5e; --paper:#f7f8fa; --card:#ffffff; --line:#e3e7ee;
    --accent:#e8622c; --accent-dark:#c94f1f; --navy:#0f2540; --navy-2:#16345c;
    --d1:#1f4e79; --d2:#6b4c9a; --d3:#1d6f68; --d4:#c94f1f; --d5:#a03453;
    color-scheme: light;
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.65;}
  a{color:var(--accent-dark);}
  code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#eef1f6;padding:1px 5px;border-radius:4px;font-size:.92em;}
  img,svg{max-width:100%;}
  .wrap{max-width:1000px;margin:0 auto;padding:0 24px;}
  .wrap-wide{max-width:1380px;margin:0 auto;padding:0 24px;}

  .nav{position:sticky;top:0;z-index:50;background:rgba(15,37,64,.96);backdrop-filter:blur(6px);border-bottom:1px solid rgba(255,255,255,.08);}
  .nav .wrap{display:flex;align-items:center;justify-content:space-between;height:56px;}
  .nav-brand{color:#fff;font-weight:700;font-size:14px;letter-spacing:.02em;text-decoration:none;}
  .nav-brand span{color:var(--accent);}
  .nav-links{display:flex;gap:22px;list-style:none;margin:0;padding:0;}
  .nav-links a{color:#cdd8e6;text-decoration:none;font-size:13.5px;font-weight:500;}
  .nav-links a:hover{color:#fff;}
  @media (max-width:720px){
    .nav .wrap{gap:12px;}
    .nav-links{gap:16px;overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;flex:1;justify-content:flex-end;}
    .nav-links::-webkit-scrollbar{display:none;}
    .nav-links a{white-space:nowrap;font-size:13px;}
  }

  header.hero{background:linear-gradient(180deg,var(--navy) 0%, var(--navy-2) 100%);color:#fff;padding:40px 0 32px;}
  .eyebrow{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#ffd8c4;background:rgba(232,98,44,.18);border:1px solid rgba(232,98,44,.4);padding:5px 10px;border-radius:999px;margin-bottom:14px;}
  h1{font-size:clamp(24px,3.6vw,34px);line-height:1.15;margin:0;font-weight:800;}
  header.hero p{font-size:15.5px;color:#c9d5e3;max-width:720px;margin:12px 0 0;}
  header.hero p a{color:#ffd8c4;}

  section{padding:34px 0;}
  h2.sh{font-size:20px;font-weight:800;margin:0 0 6px;}
  p.sl{font-size:14.5px;color:var(--ink-soft);margin:0 0 22px;max-width:760px;}

  footer{padding:32px 0 48px;color:#8b96a5;font-size:12.5px;}
  footer .wrap{border-top:1px solid var(--line);padding-top:22px;}
  footer a{color:#6b7686;}
"""

FOOTER = """<footer>
  <div class="wrap">
    <p>This is an independent, unofficial study resource and is not affiliated with, endorsed by, or sponsored by Amazon Web Services, Inc. AWS, Amazon Bedrock, and all related marks are trademarks of Amazon.com, Inc. or its affiliates.</p>
    <p>Hosted on Amazon S3 + Amazon CloudFront.</p>
  </div>
</footer>

</body>
</html>"""


def nav(links):
    items = "\n".join(f'      <li><a href="{h}">{t}</a></li>' for t, h in links)
    return f"""<nav class="nav">
  <div class="wrap">
    <a class="nav-brand" href="../index.html">AIP-C01 <span>Guide</span></a>
    <ul class="nav-links">
{items}
    </ul>
  </div>
</nav>"""


def page(title, desc, css, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<style>{BASE_CSS}{css}</style>
</head>
<body>

{body}

{FOOTER}"""


# --------------------------------------------------------------------------- #
#  concepts.html
# --------------------------------------------------------------------------- #
CONCEPTS_CSS = """
  .bar{position:sticky;top:56px;z-index:40;background:rgba(247,248,250,.97);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:12px 0;}
  .bar .wrap{display:flex;flex-wrap:wrap;gap:10px;align-items:center;}
  #q{flex:1;min-width:220px;font:inherit;font-size:14px;padding:9px 13px;border:1px solid var(--line);border-radius:9px;background:#fff;color:var(--ink);}
  #q:focus{outline:2px solid rgba(232,98,44,.35);border-color:var(--accent);}
  .chips{display:flex;gap:6px;flex-wrap:wrap;}
  .chips button{font:inherit;font-size:12.5px;font-weight:700;padding:7px 12px;border-radius:999px;border:1px solid var(--line);background:#fff;color:var(--ink-soft);cursor:pointer;}
  .chips button:hover{border-color:var(--accent);}
  .chips button[aria-pressed="true"]{color:#fff;border-color:transparent;}
  .chips button[data-d="1"][aria-pressed="true"]{background:var(--d1);}
  .chips button[data-d="2"][aria-pressed="true"]{background:var(--d2);}
  .chips button[data-d="3"][aria-pressed="true"]{background:var(--d3);}
  .chips button[data-d="4"][aria-pressed="true"]{background:var(--d4);}
  .chips button[data-d="5"][aria-pressed="true"]{background:var(--d5);}
  #tally{font-size:12.5px;color:var(--ink-soft);font-weight:600;white-space:nowrap;}

  section.grp{padding:28px 0 10px;}
  .ghead{display:flex;align-items:baseline;gap:12px;margin:0 0 6px;flex-wrap:wrap;}
  .ghead .gl{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;font-weight:700;color:#fff;background:var(--navy);padding:4px 10px;border-radius:7px;}
  .ghead h2{margin:0;font-size:19px;font-weight:800;}
  .gsub{font-size:14px;color:var(--ink-soft);margin:0 0 20px;max-width:760px;}

  figure.dia{margin:0 0 22px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;}
  figure.dia .dh{font-size:15px;font-weight:800;margin:0 0 2px;}
  figure.dia .ds{font-size:13px;color:var(--ink-soft);margin:0 0 12px;}
  .scroller{overflow-x:auto;-webkit-overflow-scrolling:touch;}
  .scroller svg{display:block;min-width:1150px;width:100%;height:auto;}
  .scroller svg a text{cursor:pointer;}
  .scroller svg a:hover text{text-decoration:underline;}
  .hint{display:none;font-size:12.5px;color:var(--ink-soft);margin:0 0 8px;font-style:italic;}
  @media (max-width:1200px){ .hint{display:block;} }

  .cc{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:18px 22px 20px;margin-bottom:14px;scroll-margin-top:124px;}
  .cc.hide{display:none;}
  .cch{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:12px;}
  .cch h3{margin:0;font-size:17px;font-weight:800;}
  .cch .cnt{font-size:11.5px;font-weight:700;color:var(--ink-soft);background:#eef1f6;border-radius:999px;padding:3px 9px;white-space:nowrap;}
  .cch .anch{font-size:12px;font-weight:700;text-decoration:none;color:#b9c2cf;margin-left:auto;}
  .cch .anch:hover{color:var(--accent);}

  .own{background:#f4f7fb;border:1px solid #dfe6f0;border-left:4px solid var(--navy-2);border-radius:10px;padding:13px 16px;margin-bottom:14px;}
  .own .lab{display:block;font-size:10.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#7d8899;margin-bottom:7px;}
  .own p{margin:9px 0 0;font-size:13.5px;color:var(--ink-soft);}
  .own p b{color:var(--ink);}
  .own.noown{border-left-color:var(--accent);background:#fdf4f0;border-color:#f3dfd6;}

  .pill{display:inline-block;color:#fff;font-size:12.5px;font-weight:700;text-decoration:none;border-radius:8px;padding:4px 11px;}
  .pill:hover{filter:brightness(1.12);}
  .d1{background:var(--d1);} .d2{background:var(--d2);} .d3{background:var(--d3);}
  .d4{background:var(--d4);} .d5{background:var(--d5);}

  ul.also{list-style:none;margin:0;padding:0;}
  ul.also li{display:flex;gap:11px;align-items:flex-start;padding:9px 0;border-top:1px solid var(--line);}
  ul.also li:first-child{border-top:none;padding-top:2px;}
  .mini{flex:0 0 auto;color:#fff;font-size:11.5px;font-weight:700;text-decoration:none;border-radius:7px;padding:2px 8px;margin-top:2px;}
  .mini:hover{filter:brightness(1.12);}
  ul.also .say{font-size:13.5px;color:var(--ink-soft);}
  ul.also .say b{color:var(--ink);font-weight:700;}

  .empty{display:none;background:var(--card);border:1px dashed var(--line);border-radius:13px;padding:28px;text-align:center;font-size:14px;color:var(--ink-soft);}
  .empty.show{display:block;}
"""


def render_card(c):
    name = c["name"]
    sl = slug(name)
    tasks = []
    if c.get("owner"):
        tasks.append(c["owner"][0])
    tasks += [a[0] for a in c["also"]]
    doms = sorted({t[0] for t in tasks})
    terms = (c["terms"] + " " + strip_tags(name)).lower()

    o = [f'    <article class="cc" id="{sl}" data-doms="{" ".join(doms)}" data-t="{terms}">',
         '      <div class="cch">',
         f'        <h3>{name}</h3>',
         f'        <span class="cnt">{len(tasks)} of 20 tasks</span>',
         f'        <a class="anch" href="#{sl}" aria-label="Link to this concept">#</a>',
         '      </div>']

    if c.get("owner"):
        t, anc, label, why = c["owner"]
        o += ['      <div class="own">',
              '        <span class="lab">The detail lives here</span>',
              f'        <a class="pill d{t[0]}" href="{href(t, anc)}">{t} &middot; {label}</a>',
              f'        <p>{why}</p>',
              '      </div>']
    else:
        o += ['      <div class="own noown">',
              '        <span class="lab">No single owner &mdash; that is the point</span>',
              f'        <p>{c["lead"]}</p>',
              '      </div>']

    o.append('      <ul class="also">')
    for t, anc, bold, rest in c["also"]:
        o += ['        <li>',
              f'          <a class="mini d{t[0]}" href="{href(t, anc)}">{t}</a>',
              f'          <div class="say"><b>{bold}</b> {rest}</div>',
              '        </li>']
    o += ['      </ul>', '    </article>']
    return "\n".join(o)


def build_concepts():
    group_dia = {"A": ["rag-path", "ingest"], "B": ["cascade"], "E": ["guardrail"],
                 "F": ["evalloop"], "G": ["resilience"]}
    body = [nav([("All Study Notes", "index.html"), ("The Whole Map", "map.html"),
                 ("Concept Index", "concepts.html"), ("Build Log", "../tasks/index.html")]),
            """
<header class="hero">
  <div class="wrap">
    <span class="eyebrow">Cross-Domain Reference</span>
    <h1>One Concept, Every Place It Appears</h1>
    <p>Some ideas turn up in a dozen tasks. That is not repetition &mdash; each task uses the same thing for a
    different job, and knowing <em>which task owns the detail</em> is half the battle. Every entry below names
    the one page to read, then says what each other task adds, and why it differs there.
    Built from all 20 sets of notes. Start with <a href="map.html">the whole map</a> if you want the shape first.</p>
  </div>
</header>

<div class="bar">
  <div class="wrap">
    <input id="q" type="search" placeholder="Search &mdash; chunking, jitter, drift&hellip;" autocomplete="off">
    <div class="chips" id="dchips">"""
            + "".join(f'\n      <button data-d="{n}" aria-pressed="false">Domain {n}</button>' for n, _, _, _ in DOMAINS)
            + """
      <button data-d="clear" aria-pressed="false">Show all</button>
    </div>
    <span id="tally"></span>
  </div>
</div>
"""]

    for gl, gname, gsub in GROUPS:
        items = [c for c in CONCEPTS if c["g"] == gl]
        body.append(f'\n<section class="grp" id="g{gl}">')
        body.append('  <div class="wrap">')
        body.append(f'    <div class="ghead"><span class="gl">Group {gl}</span><h2>{gname}</h2></div>')
        body.append(f'    <p class="gsub">{gsub}</p>')
        body.append('  </div>')
        if group_dia.get(gl):
            body.append('  <div class="wrap-wide">')
            for key in group_dia[gl]:
                head, sub, fn = DIAGRAMS[key]
                body.append(f'    <figure class="dia">\n      <p class="dh">{head}</p>\n      <p class="ds">{sub}</p>'
                            f'\n      <p class="hint">Scroll the diagram sideways if it does not fit.</p>'
                            f'\n      <div class="scroller">\n{fn()}\n      </div>\n    </figure>')
            body.append('  </div>')
        body.append('  <div class="wrap">')
        for c in items:
            body.append(render_card(c))
        body.append('  </div>\n</section>')

    body.append("""
<section style="padding-top:8px;">
  <div class="wrap">
    <div class="empty" id="empty">Nothing matches that. Try a shorter word, or <a href="#" id="reset">show everything</a>.</div>
  </div>
</section>

<script>
(function(){
  var q = document.getElementById('q'),
      cards = Array.prototype.slice.call(document.querySelectorAll('.cc')),
      chips = Array.prototype.slice.call(document.querySelectorAll('#dchips button')),
      tally = document.getElementById('tally'),
      empty = document.getElementById('empty'),
      dom = null;

  function apply(){
    var term = q.value.trim().toLowerCase(), shown = 0;
    cards.forEach(function(c){
      var okT = !term || c.getAttribute('data-t').indexOf(term) !== -1
                      || c.textContent.toLowerCase().indexOf(term) !== -1,
          okD = !dom || c.getAttribute('data-doms').split(' ').indexOf(dom) !== -1;
      if (okT && okD){ c.classList.remove('hide'); shown++; }
      else { c.classList.add('hide'); }
    });
    Array.prototype.forEach.call(document.querySelectorAll('section.grp'), function(s){
      s.style.display = s.querySelectorAll('.cc:not(.hide)').length ? '' : 'none';
    });
    tally.textContent = shown + (shown === 1 ? ' concept' : ' concepts');
    empty.classList.toggle('show', shown === 0);
  }

  q.addEventListener('input', apply);
  chips.forEach(function(b){
    b.addEventListener('click', function(){
      var d = b.getAttribute('data-d');
      dom = (d === 'clear' || dom === d) ? null : d;
      chips.forEach(function(x){
        x.setAttribute('aria-pressed', String(x.getAttribute('data-d') === dom));
      });
      apply();
    });
  });
  document.getElementById('reset').addEventListener('click', function(e){
    e.preventDefault(); q.value = ''; dom = null;
    chips.forEach(function(x){ x.setAttribute('aria-pressed','false'); });
    apply();
  });
  apply();
})();
</script>""")

    html = page("Concept Index | AIP-C01 Guide",
                "Every recurring concept in the AWS Certified Generative AI Developer (AIP-C01) notes, with the one "
                "task that owns the detail and what each other task adds.",
                CONCEPTS_CSS, "\n".join(body))
    open(f"{OUT}/concepts.html", "w").write(html)
    return len(CONCEPTS)


# --------------------------------------------------------------------------- #
#  map.html
# --------------------------------------------------------------------------- #
def d_wholemap():
    h = 562
    o = svg_open(h, "The whole exam as one request's life, in two bands. The top band follows a single request "
        "through all five domains in order. Domain 1, thirty-one percent: design it &mdash; decide the shape, pick "
        "the model, prepare the data, choose where vectors live, tune retrieval, and govern the prompt. Domain 2, "
        "twenty-six percent: build it &mdash; agents that decide their own next step, where the model physically "
        "runs, integration with systems that cannot be rewritten, and calling the model like a production "
        "dependency. Domain 3, twenty percent: guard it &mdash; stop bad input going in and bad output coming out, "
        "keep the data private, and be able to prove a year later how the model was built and who approved it. "
        "Domain 4, twelve percent: run it &mdash; what it costs, how fast it feels, and how you would notice the "
        "answers getting worse. Domain 5, eleven percent: prove it &mdash; judge whether it is good enough without "
        "a single correct answer to check against, and work out which component actually failed once it is live. "
        "The bottom band shows the threads that run through all five domains rather than belonging to any one of "
        "them: token economics, which appears in every single task; confidence thresholds, where one number "
        "gates five different decisions; guardrails and layered defense; drift, which means five unrelated "
        "things; and Step Functions with CloudWatch, which appear almost everywhere doing a different job each "
        "time. Each thread links to the concept index.")
    o += band_head(34, 16, 700, "ONE REQUEST, FIVE DOMAINS", "In the order the work actually happens")
    xs = row_x(5)
    y = 58
    bands = [
        ("1", "Design it", ["Decide the shape, pick the model,", "prepare the data, choose where", "the vectors live, tune retrieval."],
         ["6 tasks", "31%"], "domain-1.html", "Domain 1 map"),
        ("2", "Build it", ["Agents that choose their own next", "step, where the model runs, and", "calling it like a dependency."],
         ["5 tasks", "26%"], "domain-2.html", "Domain 2 map"),
        ("3", "Guard it", ["Bad input out, bad output in, the", "person out of the data &mdash; and a", "record that survives an audit."],
         ["4 tasks", "20%"], "domain-3.html", "Domain 3 map"),
        ("4", "Run it", ["What it costs, how fast it feels,", "and how you would notice the", "answers quietly getting worse."],
         ["3 tasks", "12%"], "domain-4.html", "Domain 4 map"),
        ("5", "Prove it", ["Good enough to ship, with no", "single right answer to check", "against &mdash; then which part broke."],
         ["2 tasks", "11%"], "domain-5.html", "Domain 5 map"),
    ]
    for i, (dom, t, lines, chips, hr, lt) in enumerate(bands):
        o += box(xs[i], y, DOM_COLOR[dom], t, lines, chips, dom, hr, lt)
        if i < 4:
            o += arrow(xs[i] + BOX_W, xs[i + 1], y + BOX_H / 2)

    o += band_head(34, 282, 700, "THE THREADS THROUGH ALL FIVE", "These belong to no single domain")
    xs2 = row_x(5)
    y2 = 324
    threads = [
        ("4", "Token economics", ["Billed twice, unevenly, and output", "costs more. The only concept in", "all 20 tasks without exception."],
         ["20 / 20"], "concepts.html#token-economics", "Concept index"),
        ("2", "Confidence", ["0.7 to 0.9 gates a bigger model,", "a human, a clarifying question,", "a disclaimer &mdash; five tasks, five jobs."],
         ["15 tasks"], "concepts.html#confidence-thresholds", "Concept index"),
        ("3", "Layered defense", ["Nothing is checked once. Cheapest", "filter first, because the model is", "the expensive part of the chain."],
         ["13 tasks"], "concepts.html#guardrails", "Concept index"),
        ("3", "Drift", ["Data, embedding, prompt, agent", "and latency drift are five", "unrelated things, one word."],
         ["11 tasks"], "concepts.html#drift-five-unrelated-things", "Concept index"),
        ("1", "The two everywhere", ["Step Functions in 14 tasks and", "CloudWatch in 16 &mdash; doing a", "different job in each of them."],
         ["14 &amp; 16"], "concepts.html#step-functions-twelve-unrelated-jobs", "Concept index"),
    ]
    for i, (dom, t, lines, chips, hr, lt) in enumerate(threads):
        o += box(xs2[i], y2, DOM_COLOR[dom], t, lines, chips, "all", hr, lt)
    o += note(K.CANVAS_W / 2, 536,
              "Read down for the shape of the exam; read across the bottom for the ideas that keep reappearing "
              "and will not sit still in one domain.", anchor="middle")
    return K.numeric("\n".join(o + svg_close()))


MAP_CSS = """
  figure.map{margin:0;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;}
  .scroller{overflow-x:auto;-webkit-overflow-scrolling:touch;}
  .scroller svg{display:block;min-width:1150px;width:100%;height:auto;}
  .scroller svg a text{cursor:pointer;}
  .scroller svg a:hover text{text-decoration:underline;}
  figure.map figcaption{margin-top:14px;font-size:13px;color:var(--ink-soft);text-align:center;}
  .hint{display:none;font-size:12.5px;color:var(--ink-soft);margin:0 0 8px;font-style:italic;}
  @media (max-width:1200px){ .hint{display:block;} }

  .lad{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px;}
  .step{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:18px 20px;}
  .step .n{display:inline-block;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;font-weight:700;color:#fff;background:var(--navy);border-radius:7px;padding:3px 9px;margin-bottom:9px;}
  .step h3{margin:0 0 6px;font-size:15.5px;font-weight:800;}
  .step p{margin:0 0 12px;font-size:13.5px;color:var(--ink-soft);}
  .step a.go{font-size:13px;font-weight:700;text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:7px 13px;display:inline-block;}
  .step a.go:hover{border-color:var(--accent);}
"""


def build_map():
    body = [nav([("All Study Notes", "index.html"), ("The Whole Map", "map.html"),
                 ("Concept Index", "concepts.html"), ("Build Log", "../tasks/index.html")]),
            """
<header class="hero">
  <div class="wrap">
    <span class="eyebrow">The Whole Exam</span>
    <h1>Five Domains, One Request</h1>
    <p>The five domain maps each show one stage well, but nothing shows how they join up. This is the layer
    above them: a single request being designed, built, guarded, run and proved &mdash; with the ideas that refuse
    to sit inside any one domain pulled out underneath.</p>
  </div>
</header>

<section style="padding-bottom:12px;">
  <div class="wrap-wide">
    <p class="hint">Scroll the diagram sideways if it does not fit.</p>
    <figure class="map">
      <div class="scroller">
""" + d_wholemap() + """
      </div>
      <figcaption>Every box is a link. The top row opens that domain&rsquo;s own map; the bottom row opens the concept index at that thread.</figcaption>
    </figure>
  </div>
</section>

<section style="padding-top:14px;">
  <div class="wrap">
    <h2 class="sh">How to use the three levels</h2>
    <p class="sl">The site is deliberately a pyramid. Each level answers a different question, and skipping
    straight to the bottom is how revision turns into 3,000 lines of disconnected facts.</p>
    <div class="lad">
      <div class="step">
        <span class="n">Level 1</span>
        <h3>This page</h3>
        <p>What shape is the exam, and roughly where does my weak area sit? Read once, come back when you feel lost.</p>
        <a class="go" href="map.html">You are here</a>
      </div>
      <div class="step">
        <span class="n">Level 2</span>
        <h3>The five domain maps</h3>
        <p>How do the tasks inside one domain fit together, and what is each one actually about? One picture per domain.</p>
        <a class="go" href="index.html">Pick a domain &rarr;</a>
      </div>
      <div class="step">
        <span class="n">Level 3</span>
        <h3>The 20 task pages</h3>
        <p>The notes themselves, verbatim, with the architecture diagram for that task. Where the detail actually lives.</p>
        <a class="go" href="index.html">All study notes &rarr;</a>
      </div>
      <div class="step">
        <span class="n">Sideways</span>
        <h3>The concept index</h3>
        <p>Cuts across all three. One entry per recurring idea, naming the task that owns it and what every other task adds.</p>
        <a class="go" href="concepts.html">Concept index &rarr;</a>
      </div>
    </div>
  </div>
</section>"""]
    html = page("The Whole Map | AIP-C01 Guide",
                "One diagram of how all five domains of the AWS Certified Generative AI Developer (AIP-C01) exam "
                "join up as a single request, plus the concepts that cut across every domain.",
                MAP_CSS, "\n".join(body))
    open(f"{OUT}/map.html", "w").write(html)


# --------------------------------------------------------------------------- #
#  index.html
# --------------------------------------------------------------------------- #
INDEX_CSS = """
  .start{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin-bottom:10px;}
  .scard{display:block;text-decoration:none;color:inherit;border-radius:14px;padding:20px 22px;border:1px solid var(--line);background:var(--card);transition:border-color .15s;}
  .scard:hover{border-color:var(--accent);}
  .scard .k{display:inline-block;font-size:10.5px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;padding:3px 9px;border-radius:999px;margin-bottom:9px;}
  .scard h3{margin:0 0 6px;font-size:16px;font-weight:800;}
  .scard p{margin:0;font-size:13.5px;color:var(--ink-soft);}
  .scard .tref{display:block;margin-top:10px;font-size:12.5px;color:var(--accent-dark);font-weight:700;}
  .scard.hi{background:linear-gradient(135deg,#132b4b 0%,#1b3c68 100%);border-color:#1b3c68;color:#fff;}
  .scard.hi h3{color:#fff;} .scard.hi p{color:#c9d5e3;} .scard.hi .tref{color:#ffd8c4;}
  .scard.hi .k{color:#ffd8c4;background:rgba(232,98,44,.22);border:1px solid rgba(232,98,44,.45);}
  .scard .k{color:var(--navy-2);background:#eef1f6;}

  .weights{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:6px;}
  @media (max-width:760px){ .weights{grid-template-columns:repeat(2,1fr);} }
  .w{display:block;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--line);border-top:4px solid var(--line);border-radius:12px;padding:14px 15px;transition:border-color .15s;}
  .w:hover{border-color:var(--accent);}
  .w .pct{font-size:24px;font-weight:800;line-height:1;}
  .w .dn{font-size:11.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#8b96a5;margin-bottom:7px;}
  .w .tk{font-size:12.5px;color:var(--ink-soft);margin-top:5px;}
  .w1{border-top-color:var(--d1);} .w2{border-top-color:var(--d2);} .w3{border-top-color:var(--d3);}
  .w4{border-top-color:var(--d4);} .w5{border-top-color:var(--d5);}
  .w1 .pct{color:var(--d1);} .w2 .pct{color:var(--d2);} .w3 .pct{color:var(--d3);}
  .w4 .pct{color:var(--d4);} .w5 .pct{color:var(--d5);}

  .domain-head{display:flex;align-items:center;gap:12px;margin:38px 0 16px;}
  .domain-head .dnum{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;font-weight:700;color:#fff;background:var(--navy);padding:5px 11px;border-radius:7px;white-space:nowrap;}
  .domain-head h2{margin:0;font-size:17px;font-weight:800;color:var(--ink);}
  .domain-head .wt{font-size:12px;font-weight:700;color:var(--ink-soft);background:#eef1f6;border-radius:999px;padding:3px 9px;}
  .domain-head .dline{flex:1;height:1px;background:var(--line);}

  .task-card{background:var(--card);border:1px solid var(--line);border-radius:14px;border-left:4px solid var(--line);padding:18px 22px;margin-bottom:11px;display:block;text-decoration:none;color:inherit;transition:border-color .15s;}
  .task-card:hover{border-color:var(--accent);}
  .task-card h3{margin:0 0 5px;font-size:15.5px;font-weight:700;color:var(--ink);}
  .task-card p{margin:0;font-size:13.5px;color:var(--ink-soft);}
  .task-card .cg{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px;}
  .task-card .cg span{font-size:11px;font-weight:600;color:#4a5a70;background:#eef2f7;border:1px solid #e3e8ef;border-radius:6px;padding:2px 8px;}
  .task-card .tref{display:block;margin-top:10px;font-size:12px;color:var(--accent-dark);font-weight:600;}
  .tl1{border-left-color:var(--d1);} .tl2{border-left-color:var(--d2);} .tl3{border-left-color:var(--d3);}
  .tl4{border-left-color:var(--d4);} .tl5{border-left-color:var(--d5);}

  .task-card.master{background:linear-gradient(135deg,#132b4b 0%,#1b3c68 100%);border-color:#1b3c68;border-left-color:var(--accent);color:#fff;}
  .task-card.master:hover{border-color:var(--accent);}
  .task-card.master h3{color:#fff;} .task-card.master p{color:#c9d5e3;} .task-card.master .tref{color:#ffd8c4;}
  .task-card.master .mtag{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#ffd8c4;background:rgba(232,98,44,.22);border:1px solid rgba(232,98,44,.45);padding:3px 8px;border-radius:999px;margin-bottom:8px;}
"""

MAP_BLURB = {
 "1": "How all six tasks fit together, in three steps and one picture &mdash; plus a plain-English summary of what each task is actually about.",
 "2": "How all five tasks fit together as one request &mdash; getting in, deciding what to do, and the work that never stops.",
 "3": "How all four tasks fit together &mdash; what gets checked before the model, what gets checked after it, and what you write down either way.",
 "4": "How all three tasks fit together as one running system &mdash; what it costs, how fast it feels, and how you would know if either changed.",
 "5": "How both tasks fit together &mdash; judging whether it is good enough to ship, and working out which part broke once it has.",
}


def build_index():
    by_dom = {}
    for t in sorted(TASKS):
        by_dom.setdefault(t[0], []).append(t)

    body = [nav([("Domains", "../index.html#domains"), ("The Whole Map", "map.html"),
                 ("Concept Index", "concepts.html"), ("Study Notes", "index.html"),
                 ("Build Log", "../tasks/index.html"), ("Quiz", "../quiz/index.html")]),
            f"""
<header class="hero">
  <div class="wrap">
    <span class="eyebrow">Personal Cheat Sheets</span>
    <h1>Study Notes</h1>
    <p>Twenty tasks across five domains, written out in full &mdash; plus a map per domain, a map of the whole exam,
    and a cross-domain index for the ideas that appear in a dozen places at once.</p>
  </div>
</header>

<section style="padding-bottom:6px;">
  <div class="wrap">
    <h2 class="sh">Start here</h2>
    <p class="sl">Three ways in, depending on what you are trying to do right now.</p>
    <div class="start">
      <a class="scard hi" href="map.html">
        <span class="k">Level 1</span>
        <h3>The whole exam, one picture</h3>
        <p>All five domains as a single request being designed, built, guarded, run and proved. Read this first if the 20 pages below feel like a pile.</p>
        <span class="tref">Open the map &rarr;</span>
      </a>
      <a class="scard" href="concepts.html">
        <span class="k">Sideways</span>
        <h3>Concept index</h3>
        <p>{len(CONCEPTS)} recurring ideas, each naming the one task that owns the detail and what every other task adds. For when two pages seem to disagree.</p>
        <span class="tref">Open the index &rarr;</span>
      </a>
      <a class="scard" href="#d1">
        <span class="k">Level 2 &amp; 3</span>
        <h3>Straight to the notes</h3>
        <p>Domain by domain below, each with its own map followed by the task pages. Every task card says what that task is actually about.</p>
        <span class="tref">Jump to Domain 1 &rarr;</span>
      </a>
    </div>
  </div>
</section>

<section style="padding-top:20px;padding-bottom:6px;">
  <div class="wrap">
    <h2 class="sh">Where the marks are</h2>
    <p class="sl">Domains 1 and 2 are 57% of the exam between them. Domain 4 carries only 12% but the densest
    notes on cost, which is worth knowing before you budget your revision.</p>
    <div class="weights">"""]

    for n, title, pct, _ in DOMAINS:
        cnt = len(by_dom[n])
        body.append(f"""      <a class="w w{n}" href="domain-{n}.html">
        <div class="dn">Domain {n}</div>
        <div class="pct">{pct}</div>
        <div class="tk">{cnt} task{"s" if cnt > 1 else ""}</div>
      </a>""")
    body.append("    </div>\n  </div>\n</section>\n\n<section style=\"padding-top:14px;\">\n  <div class=\"wrap\">")

    for n, title, pct, _ in DOMAINS:
        body.append(f"""
    <div class="domain-head" id="d{n}">
      <span class="dnum">Domain {n}</span>
      <h2>{title}</h2>
      <span class="wt">{pct}</span>
      <span class="dline"></span>
    </div>

    <a class="task-card master" href="domain-{n}.html">
      <span class="mtag">Start here</span>
      <h3>Domain {n} &#8212; The Map</h3>
      <p>{MAP_BLURB[n]}</p>
      <span class="tref">View the map &rarr;</span>
    </a>""")
        for t in by_dom[n]:
            tt, one, chips = TASKS[t]
            cg = "".join(f"<span>{c}</span>" for c in chips)
            body.append(f"""
    <a class="task-card tl{n}" href="task-{t.replace('.', '-')}.html">
      <h3>Task {t} &#8212; {tt}</h3>
      <p>{one}</p>
      <div class="cg">{cg}</div>
      <span class="tref">View notes &rarr;</span>
    </a>""")

    body.append("\n  </div>\n</section>")
    html = page("Study Notes | AIP-C01 Guide",
                "Personal cheat sheets, domain maps and a cross-domain concept index for the AWS Certified "
                "Generative AI Developer - Professional (AIP-C01) exam, organized by domain and task.",
                INDEX_CSS, "\n".join(body))
    open(f"{OUT}/index.html", "w").write(html)


if __name__ == "__main__":
    n = build_concepts()
    build_map()
    build_index()
    print(f"concepts.html  {n} concepts")
    for f in ("concepts.html", "map.html", "index.html"):
        print(f"  {f:16s} {os.path.getsize(OUT + '/' + f):>8,} bytes")
