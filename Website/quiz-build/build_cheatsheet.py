# -*- coding: utf-8 -*-
"""Builds Website/src/quiz/cheatsheet.html from cheatsheet.py."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cheatsheet import SETS

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "quiz", "cheatsheet.html")
TOTAL_SETS = 9

CSS = """
  :root{
    --ink:#0b1524; --ink-soft:#4a5a6e; --paper:#f7f8fa; --card:#ffffff; --line:#e3e7ee;
    --accent:#e8622c; --accent-dark:#c94f1f; --navy:#0f2540; --navy-2:#16345c;
    color-scheme: light;
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.55;}
  a{color:var(--accent-dark);}
  .wrap{max-width:1020px;margin:0 auto;padding:0 24px;}

  .nav{position:sticky;top:0;z-index:60;background:rgba(15,37,64,.96);backdrop-filter:blur(6px);}
  .nav .wrap{display:flex;align-items:center;justify-content:space-between;height:56px;max-width:1080px;}
  .nav-brand{color:#fff;font-weight:700;font-size:14px;text-decoration:none;}
  .nav-brand span{color:var(--accent);}
  .nav-links{display:flex;gap:22px;list-style:none;margin:0;padding:0;}
  .nav-links a{color:#cdd8e6;text-decoration:none;font-size:13.5px;font-weight:500;}
  .nav-links a:hover{color:#fff;}
  @media (max-width:720px){
    .nav-links{gap:16px;overflow-x:auto;scrollbar-width:none;flex:1;justify-content:flex-end;}
    .nav-links::-webkit-scrollbar{display:none;}
    .nav-links a{white-space:nowrap;font-size:13px;}
  }

  header.hero{background:linear-gradient(180deg,var(--navy) 0%, var(--navy-2) 100%);color:#fff;padding:36px 0 30px;}
  h1{font-size:clamp(23px,3.4vw,31px);line-height:1.15;margin:0;font-weight:800;}
  header.hero p{font-size:15px;color:#c9d5e3;max-width:620px;margin:10px 0 0;}
  header.hero p a{color:#ffd8c4;}

  .jump{position:sticky;top:56px;z-index:50;background:rgba(247,248,250,.97);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:10px 0;}
  .jump .wrap{display:flex;gap:6px;flex-wrap:wrap;align-items:center;max-width:1080px;}
  .jump a{font-size:12.5px;font-weight:700;text-decoration:none;border:1px solid var(--line);background:#fff;color:var(--ink-soft);border-radius:999px;padding:5px 12px;}
  .jump a:hover{border-color:var(--accent);color:var(--accent-dark);}
  .jump a.off{opacity:.4;pointer-events:none;}

  section.set{padding:30px 0 4px;scroll-margin-top:118px;}
  h2{margin:0 0 14px;font-size:17px;font-weight:800;}

  table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
        border-radius:11px;overflow:hidden;}
  td{padding:9px 14px;font-size:13.5px;vertical-align:top;border-top:1px solid var(--line);}
  tr:first-child td{border-top:none;}
  td.q{color:var(--ink);width:33%;}
  td.a{color:var(--ink);font-weight:700;width:28%;}
  td.w{color:var(--ink-soft);font-size:12.5px;}
  @media (max-width:720px){
    td{display:block;border-top:none;padding:3px 14px;}
    tr{display:block;border-top:1px solid var(--line);padding:7px 0;}
    tr:first-child{border-top:none;}
    td.q{font-weight:600;}
  }
  tr.trap td{background:#fdf5ee;}
  tr.trap td.a{color:#a8521c;}
  tr.trap td.a:before{content:"\\00d7  ";color:#c0536b;}

  .todo{margin-top:16px;background:#eef1f6;border:1px dashed #cdd6e2;border-radius:11px;padding:18px;
        text-align:center;font-size:13.5px;color:var(--ink-soft);}

  footer{padding:30px 0 46px;color:#8b96a5;font-size:12.5px;}
  footer .wrap{border-top:1px solid var(--line);padding-top:20px;}
"""


def build():
    done = {s[0] for s in SETS}
    jump = "".join('<a href="#set%d" class="%s">Set %d</a>' % (n, "" if n in done else "off", n)
                   for n in range(1, TOTAL_SETS + 1))

    body = []
    for n, rows in SETS:
        body.append('\n<section class="set" id="set%d">\n  <div class="wrap">' % n)
        body.append('    <h2>Set %d</h2>\n    <table>' % n)
        for q, a, w in rows:
            cls = ' class="trap"' if a.startswith("!") else ""
            body.append('      <tr%s><td class="q">%s</td><td class="a">%s</td>'
                        '<td class="w">%s</td></tr>' % (cls, q, a.lstrip("!"), w))
        body.append('    </table>\n  </div>\n</section>')

    left = [n for n in range(1, TOTAL_SETS + 1) if n not in done]
    if left:
        rng = ("Sets %d&ndash;%d" % (left[0], left[-1])) if len(left) > 1 else ("Set %d" % left[0])
        body.append('\n<section class="set">\n  <div class="wrap">'
                    '\n    <div class="todo">%s not written yet.</div>\n  </div>\n</section>' % rng)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Quiz Cheat Sheet | AIP-C01 Guide</title>
<meta name="description" content="One-line cheat sheet for the AIP-C01 practice quiz: what you see on the left, what to answer on the right.">
<style>%s</style>
</head>
<body>

<nav class="nav">
  <div class="wrap">
    <a class="nav-brand" href="../index.html">AIP-C01 <span>Guide</span></a>
    <ul class="nav-links">
      <li><a href="index.html">Quiz</a></li>
      <li><a href="cheatsheet.html">Cheat Sheet</a></li>
      <li><a href="../notes/index.html">Study Notes</a></li>
      <li><a href="../notes/map.html">The Map</a></li>
    </ul>
  </div>
</nav>

<header class="hero">
  <div class="wrap">
    <h1>Quiz Cheat Sheet</h1>
    <p>What you see, what to answer. Where two services both work, the left side says which way
    the question leans. Take the <a href="index.html">quiz</a> first.</p>
  </div>
</header>

<div class="jump">
  <div class="wrap">%s</div>
</div>
%s

<footer>
  <div class="wrap">
    <p>This is an independent, unofficial study resource and is not affiliated with, endorsed by, or sponsored by Amazon Web Services, Inc. AWS, Amazon Bedrock, and all related marks are trademarks of Amazon.com, Inc. or its affiliates.</p>
  </div>
</footer>

</body>
</html>""" % (CSS, jump, "".join(body))
    open(OUT, "w").write(html)
    print("sets %s  rows %d  %s bytes" % (sorted(done), sum(len(s[1]) for s in SETS),
                                          format(os.path.getsize(OUT), ",")))


if __name__ == "__main__":
    build()
