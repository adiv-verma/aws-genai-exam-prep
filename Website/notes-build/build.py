# -*- coding: utf-8 -*-
"""Builds notes/map.html (the pipeline map) and notes/index.html (the hub)."""
import re, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import DOMAINS, TASKS, MAP_BLURB
from pipeline import PHASES, STAGES

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "notes")
DOM_COLOR = {"1": "#1f4e79", "2": "#6b4c9a", "3": "#1d6f68", "4": "#c94f1f", "5": "#a03453"}


def strip(s):
    return re.sub(r"<[^>]+>", "", re.sub(r"&[a-z]+;|&#\d+;", " ", s))


def href(task, anc):
    return f"task-{task.replace('.', '-')}.html#{anc}"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", strip(s).lower()).strip("-")


BASE_CSS = """
  :root{
    --ink:#0b1524; --ink-soft:#3a4a5e; --paper:#f7f8fa; --card:#ffffff; --line:#e3e7ee;
    --accent:#e8622c; --accent-dark:#c94f1f; --navy:#0f2540; --navy-2:#16345c;
    --d1:#1f4e79; --d2:#6b4c9a; --d3:#1d6f68; --d4:#c94f1f; --d5:#a03453;
    color-scheme: light;
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.6;}
  a{color:var(--accent-dark);}
  img,svg{max-width:100%;}
  .wrap{max-width:1080px;margin:0 auto;padding:0 24px;}
  .wrap-wide{max-width:1380px;margin:0 auto;padding:0 24px;}

  .nav{position:sticky;top:0;z-index:60;background:rgba(15,37,64,.96);backdrop-filter:blur(6px);border-bottom:1px solid rgba(255,255,255,.08);}
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
  header.hero p{font-size:15.5px;color:#c9d5e3;max-width:740px;margin:12px 0 0;}
  header.hero p a{color:#ffd8c4;}

  section{padding:32px 0;}
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
    return f'<nav class="nav">\n  <div class="wrap">\n    <a class="nav-brand" href="../index.html">AIP-C01 <span>Guide</span></a>\n    <ul class="nav-links">\n{items}\n    </ul>\n  </div>\n</nav>'


def page(title, desc, css, body):
    return (f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'<title>{title}</title>\n<meta name="description" content="{desc}">\n'
            f'<style>{BASE_CSS}{css}</style>\n</head>\n<body>\n\n{body}\n\n{FOOTER}')


# --------------------------------------------------------------------------- #
#  The spine: nine phases, left to right, the shape of the whole pipeline
# --------------------------------------------------------------------------- #
def spine_svg(counts):
    W, H = 1282, 150
    bw, gap = 126, 11
    total = len(PHASES) * bw + (len(PHASES) - 1) * gap
    x0 = (W - total) / 2
    aria = ("The whole course as one pipeline, nine phases left to right. " +
            " ".join(f"Phase {n}, {t}: {strip(d)} {counts[k]} concepts." for k, n, t, d, _ in PHASES))
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{aria}" xmlns="http://www.w3.org/2000/svg">',
         '<defs><marker id="sa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" '
         'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#8b96a5"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#f7f8fa"/>',
         '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif">',
         f'<text x="{W/2}" y="20" text-anchor="middle" font-size="11.5" font-weight="700" fill="#8b96a5" '
         'letter-spacing=".1em">START &#8594; FINISH</text>']
    y = 34
    for i, (k, n, t, d, col) in enumerate(PHASES):
        x = x0 + i * (bw + gap)
        cx = x + bw / 2
        o += [f'<a href="#p{k}">',
              f'<rect x="{x:.1f}" y="{y}" width="{bw}" height="86" rx="11" fill="#ffffff" stroke="#d7dee8" stroke-width="1.5"/>',
              f'<rect x="{x:.1f}" y="{y}" width="{bw}" height="4" rx="2" fill="{col}"/>',
              f'<circle cx="{cx:.1f}" cy="{y+24}" r="11" fill="{col}"/>',
              f'<text x="{cx:.1f}" y="{y+28}" text-anchor="middle" font-size="12" font-weight="800" fill="#fff">{n}</text>']
        words, line = t.split(), []
        lines = []
        for w in words:
            if sum(len(x2) for x2 in line + [w]) + len(line) > 15:
                lines.append(" ".join(line)); line = [w]
            else:
                line.append(w)
        lines.append(" ".join(line))
        for li, ln in enumerate(lines[:2]):
            o.append(f'<text x="{cx:.1f}" y="{y+48+li*13}" text-anchor="middle" font-size="12.5" '
                     f'font-weight="700" fill="#0b1524">{ln}</text>')
        o.append(f'<text x="{cx:.1f}" y="{y+76}" text-anchor="middle" font-size="10.5" '
                 f'font-weight="600" fill="#8b96a5">{counts[k]} concepts</text>')
        o.append('</a>')
        if i < len(PHASES) - 1:
            o.append(f'<line x1="{x+bw+2:.1f}" y1="{y+43}" x2="{x+bw+gap-3:.1f}" y2="{y+43}" '
                     'stroke="#8b96a5" stroke-width="1.6" marker-end="url(#sa)"/>')
    o += ['</g>', '</svg>']
    return "\n".join(o)


MAP_CSS = """
  .bar{position:sticky;top:56px;z-index:50;background:rgba(247,248,250,.97);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:11px 0;}
  .bar .wrap-wide{display:flex;flex-wrap:wrap;gap:9px;align-items:center;}
  #q{flex:1;min-width:200px;font:inherit;font-size:14px;padding:9px 13px;border:1px solid var(--line);border-radius:9px;background:#fff;color:var(--ink);}
  #q:focus{outline:2px solid rgba(232,98,44,.35);border-color:var(--accent);}
  .chips{display:flex;gap:5px;flex-wrap:wrap;}
  .chips button{font:inherit;font-size:12px;font-weight:700;padding:6px 11px;border-radius:999px;border:1px solid var(--line);background:#fff;color:var(--ink-soft);cursor:pointer;}
  .chips button:hover{border-color:var(--accent);}
  .chips button[aria-pressed="true"]{color:#fff;border-color:transparent;}
  .chips button[data-d="1"][aria-pressed="true"]{background:var(--d1);}
  .chips button[data-d="2"][aria-pressed="true"]{background:var(--d2);}
  .chips button[data-d="3"][aria-pressed="true"]{background:var(--d3);}
  .chips button[data-d="4"][aria-pressed="true"]{background:var(--d4);}
  .chips button[data-d="5"][aria-pressed="true"]{background:var(--d5);}
  #tally{font-size:12.5px;color:var(--ink-soft);font-weight:600;white-space:nowrap;}

  figure.spine{margin:0;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px 10px;}
  .scroller{overflow-x:auto;-webkit-overflow-scrolling:touch;}
  .scroller svg{display:block;min-width:1180px;width:100%;height:auto;}
  .scroller svg a rect{cursor:pointer;}
  .scroller svg a:hover rect{stroke:var(--accent);}
  figure.spine figcaption{margin-top:8px;font-size:12.5px;color:var(--ink-soft);text-align:center;}
  .hint{display:none;font-size:12.5px;color:var(--ink-soft);margin:0 0 6px;font-style:italic;}
  @media (max-width:1250px){ .hint{display:block;} }

  .ph{scroll-margin-top:118px;padding:30px 0 6px;}
  .phh{display:flex;align-items:flex-start;gap:13px;margin-bottom:4px;}
  .phh .pn{flex:0 0 auto;width:34px;height:34px;border-radius:10px;color:#fff;font-size:15px;font-weight:800;display:flex;align-items:center;justify-content:center;}
  .phh h2{margin:0;font-size:21px;font-weight:800;}
  .phh .pc{font-size:11.5px;font-weight:700;color:var(--ink-soft);background:#eef1f6;border-radius:999px;padding:3px 9px;white-space:nowrap;margin-left:auto;}
  .phd{font-size:14.5px;color:var(--ink-soft);margin:0 0 16px;padding-left:47px;max-width:780px;}

  .stage{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:16px 19px 17px;margin-bottom:11px;}
  .stage h3{margin:0 0 3px;font-size:15.5px;font-weight:800;}
  .stage .sb{margin:0 0 12px;font-size:13.5px;color:var(--ink-soft);}
  .grid{display:flex;flex-wrap:wrap;gap:6px;}

  a.cx{display:inline-flex;align-items:center;gap:6px;text-decoration:none;font-size:12.5px;
       background:#f4f6fa;border:1px solid #e1e7ef;border-radius:7px;padding:4px 5px 4px 9px;color:var(--ink);transition:border-color .12s,background .12s;}
  a.cx:hover{border-color:var(--accent);background:#fff;}
  a.cx b{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10px;font-weight:700;
         color:#fff;border-radius:4px;padding:1px 4px;}
  a.cx.hide,.stage.hide,.ph.hide{display:none;}
  .b1{background:var(--d1);} .b2{background:var(--d2);} .b3{background:var(--d3);}
  .b4{background:var(--d4);} .b5{background:var(--d5);}

  .empty{display:none;background:var(--card);border:1px dashed var(--line);border-radius:13px;padding:26px;text-align:center;font-size:14px;color:var(--ink-soft);}
  .empty.show{display:block;}
"""


def build_map():
    counts = collections.Counter()
    for ph, t, b, items in STAGES:
        counts[ph] += len(items)
    total = sum(counts.values())

    body = [nav([("All Study Notes", "index.html"), ("The Map", "map.html"),
                 ("Build Log", "../tasks/index.html"), ("Quiz", "../quiz/index.html")]),
            f"""
<header class="hero">
  <div class="wrap">
    <span class="eyebrow">The Whole Course, One Pipeline</span>
    <h1>Everything, In The Order You Would Build It</h1>
    <p>Every concept in all 20 sets of notes &mdash; {total} of them &mdash; laid out as one
    generative-AI system being built end to end: framing the problem, getting the data, building the
    memory, picking the model, assembling it, shipping it, serving a request, running it, and proving
    it. Each item links to the exact section of the notes that covers it.</p>
  </div>
</header>

<section style="padding:22px 0 4px;">
  <div class="wrap-wide">
    <p class="hint">Scroll the diagram sideways if it does not fit.</p>
    <figure class="spine">
      <div class="scroller">
{spine_svg(counts)}
      </div>
      <figcaption>Nine phases, in build order. Click any phase to jump to it.</figcaption>
    </figure>
  </div>
</section>

<div class="bar">
  <div class="wrap-wide">
    <input id="q" type="search" placeholder="Search all {total} concepts &mdash; Clarify, HNSW, jitter, LoRA&hellip;" autocomplete="off">
    <div class="chips" id="dchips">"""
            + "".join(f'\n      <button data-d="{n}" aria-pressed="false">D{n}</button>' for n, _, _, _ in DOMAINS)
            + f"""
      <button data-d="clear" aria-pressed="false">All</button>
    </div>
    <span id="tally">{total} concepts</span>
  </div>
</div>
"""]

    for k, n, title, blurb, col in PHASES:
        body.append(f'\n<section class="ph" id="p{k}">\n  <div class="wrap">')
        body.append(f'    <div class="phh"><span class="pn" style="background:{col}">{n}</span>'
                    f'<h2>{title}</h2><span class="pc">{counts[k]} concepts</span></div>')
        body.append(f'    <p class="phd">{blurb}</p>')
        for ph, st, sb, items in STAGES:
            if ph != k:
                continue
            body.append(f'    <div class="stage" id="s-{slug(st)}">')
            body.append(f'      <h3>{st}</h3>\n      <p class="sb">{sb}</p>\n      <div class="grid">')
            for lab, t, a in items:
                body.append(f'        <a class="cx" data-d="{t[0]}" data-t="{strip(lab).lower()}" '
                            f'href="{href(t, a)}">{lab}<b class="b{t[0]}">{t}</b></a>')
            body.append('      </div>\n    </div>')
        body.append('  </div>\n</section>')

    body.append("""
<section style="padding-top:6px;">
  <div class="wrap">
    <div class="empty" id="empty">Nothing matches that. Try a shorter word, or <a href="#" id="reset">show everything</a>.</div>
  </div>
</section>

<script>
(function(){
  var q=document.getElementById('q'),
      cx=[].slice.call(document.querySelectorAll('a.cx')),
      stages=[].slice.call(document.querySelectorAll('.stage')),
      phases=[].slice.call(document.querySelectorAll('.ph')),
      chips=[].slice.call(document.querySelectorAll('#dchips button')),
      tally=document.getElementById('tally'),
      empty=document.getElementById('empty'),
      dom=null;

  function apply(){
    var term=q.value.trim().toLowerCase(), shown=0;
    cx.forEach(function(a){
      var ok=(!term||a.getAttribute('data-t').indexOf(term)!==-1)&&
             (!dom||a.getAttribute('data-d')===dom);
      if(ok){a.classList.remove('hide');shown++;}else{a.classList.add('hide');}
    });
    stages.forEach(function(s){
      s.classList.toggle('hide', !s.querySelectorAll('a.cx:not(.hide)').length);
    });
    phases.forEach(function(p){
      p.classList.toggle('hide', !p.querySelectorAll('.stage:not(.hide)').length);
    });
    tally.textContent=shown+(shown===1?' concept':' concepts');
    empty.classList.toggle('show',shown===0);
  }
  q.addEventListener('input',apply);
  chips.forEach(function(b){
    b.addEventListener('click',function(){
      var d=b.getAttribute('data-d');
      dom=(d==='clear'||dom===d)?null:d;
      chips.forEach(function(x){x.setAttribute('aria-pressed',String(x.getAttribute('data-d')===dom));});
      apply();
    });
  });
  document.getElementById('reset').addEventListener('click',function(e){
    e.preventDefault();q.value='';dom=null;
    chips.forEach(function(x){x.setAttribute('aria-pressed','false');});
    apply();
  });
  apply();
})();
</script>""")

    html = page("The Map | AIP-C01 Guide",
                f"All {total} concepts from the AWS Certified Generative AI Developer (AIP-C01) study notes, "
                "laid out as one AI system being built end to end, each linked to the notes that cover it.",
                MAP_CSS, "\n".join(body))
    open(f"{OUT}/map.html", "w").write(html)
    return total


# --------------------------------------------------------------------------- #
#  index.html — the study-notes hub
# --------------------------------------------------------------------------- #
INDEX_CSS = """
  .start{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;}
  .scard{display:block;text-decoration:none;color:inherit;border-radius:14px;padding:20px 22px;border:1px solid var(--line);background:var(--card);transition:border-color .15s;}
  .scard:hover{border-color:var(--accent);}
  .scard h3{margin:0 0 6px;font-size:16px;font-weight:800;}
  .scard p{margin:0;font-size:13.5px;color:var(--ink-soft);}
  .scard .tref{display:block;margin-top:10px;font-size:12.5px;color:var(--accent-dark);font-weight:700;}
  .scard .k{display:inline-block;font-size:10.5px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;padding:3px 9px;border-radius:999px;margin-bottom:9px;color:var(--navy-2);background:#eef1f6;}
  .scard.hi{background:linear-gradient(135deg,#132b4b 0%,#1b3c68 100%);border-color:#1b3c68;color:#fff;}
  .scard.hi h3{color:#fff;} .scard.hi p{color:#c9d5e3;} .scard.hi .tref{color:#ffd8c4;}
  .scard.hi .k{color:#ffd8c4;background:rgba(232,98,44,.22);border:1px solid rgba(232,98,44,.45);}

  .weights{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;}
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
  .task-card.master h3{color:#fff;} .task-card.master p{color:#c9d5e3;} .task-card.master .tref{color:#ffd8c4;}
  .task-card.master .mtag{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#ffd8c4;background:rgba(232,98,44,.22);border:1px solid rgba(232,98,44,.45);padding:3px 8px;border-radius:999px;margin-bottom:8px;}
"""


def build_index(total):
    by_dom = {}
    for t in sorted(TASKS):
        by_dom.setdefault(t[0], []).append(t)

    body = [nav([("Domains", "../index.html#domains"), ("The Map", "map.html"),
                 ("Study Notes", "index.html"), ("Build Log", "../tasks/index.html"),
                 ("Quiz", "../quiz/index.html")]),
            f"""
<header class="hero">
  <div class="wrap">
    <span class="eyebrow">Personal Cheat Sheets</span>
    <h1>Study Notes</h1>
    <p>Twenty tasks across five domains, written out in full, with a map per domain &mdash; plus
    <a href="map.html">one big map</a> that lays all {total} concepts out as a single pipeline.</p>
  </div>
</header>

<section style="padding-bottom:8px;">
  <div class="wrap">
    <div class="start">
      <a class="scard hi" href="map.html">
        <span class="k">Start here</span>
        <h3>The Map &mdash; everything, in build order</h3>
        <p>All {total} concepts from these notes as one AI system being built end to end, in nine
        phases. Searchable. Every item links straight to the section that explains it.</p>
        <span class="tref">Open the map &rarr;</span>
      </a>
      <a class="scard" href="#d1">
        <span class="k">The notes</span>
        <h3>Read them domain by domain</h3>
        <p>Each domain below opens with its own map, then one page per task. Every card says what
        that task is actually about.</p>
        <span class="tref">Jump to Domain 1 &rarr;</span>
      </a>
    </div>
  </div>
</section>

<section style="padding-top:20px;padding-bottom:6px;">
  <div class="wrap">
    <h2 class="sh">Where the marks are</h2>
    <p class="sl">Domains 1 and 2 are 57% of the exam between them. Domain 4 carries only 12% but the
    densest notes on cost, which is worth knowing before you budget your revision.</p>
    <div class="weights">"""]

    for n, title, pct, _ in DOMAINS:
        cnt = len(by_dom[n])
        body.append(f'      <a class="w w{n}" href="domain-{n}.html">\n'
                    f'        <div class="dn">Domain {n}</div>\n'
                    f'        <div class="pct">{pct}</div>\n'
                    f'        <div class="tk">{cnt} task{"s" if cnt > 1 else ""}</div>\n      </a>')
    body.append('    </div>\n  </div>\n</section>\n\n<section style="padding-top:14px;">\n  <div class="wrap">')

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
                "Personal cheat sheets and domain maps for the AWS Certified Generative AI Developer - "
                "Professional (AIP-C01) exam, organized by domain and task.",
                INDEX_CSS, "\n".join(body))
    open(f"{OUT}/index.html", "w").write(html)


if __name__ == "__main__":
    total = build_map()
    build_index(total)
    print(f"{total} concepts across {len(STAGES)} stages in {len(PHASES)} phases")
    for f in ("map.html", "index.html"):
        print(f"  {f:14s} {os.path.getsize(OUT + '/' + f):>9,} bytes")
