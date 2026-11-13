# -*- coding: utf-8 -*-
"""Builds notes/cheatsheet.html from revision.py."""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revision import TASKS, DOMAINS

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "notes", "cheatsheet.html")

CSS = """
  :root{
    --ink:#0b1524; --ink-soft:#44556b; --paper:#f7f8fa; --card:#fff; --line:#e3e7ee;
    --accent:#e8622c; --accent-dark:#c94f1f; --navy:#0f2540; --navy-2:#16345c;
    --d1:#1f4e79; --d2:#6b4c9a; --d3:#1d6f68; --d4:#c94f1f; --d5:#a03453;
    color-scheme: light;
  }
  *{box-sizing:border-box;}
  [hidden]{display:none !important;}
  html{scroll-behavior:smooth;}
  body{margin:0;background:var(--paper);color:var(--ink);
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.5;}
  a{color:var(--accent-dark);}
  code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#eef1f6;padding:1px 4px;border-radius:4px;font-size:.92em;}
  .wrap{max-width:1180px;margin:0 auto;padding:0 24px;}

  .nav{background:var(--navy);}
  .nav .wrap{display:flex;align-items:center;justify-content:space-between;height:56px;}
  .nav-brand{color:#fff;font-weight:700;font-size:14px;text-decoration:none;}
  .nav-brand span{color:var(--accent);}
  .nav-links{display:flex;gap:20px;list-style:none;margin:0;padding:0;}
  .nav-links a{color:#cdd8e6;text-decoration:none;font-size:13.5px;font-weight:500;}
  .nav-links a:hover{color:#fff;}
  @media (max-width:720px){
    .nav-links{gap:15px;overflow-x:auto;scrollbar-width:none;flex:1;justify-content:flex-end;}
    .nav-links::-webkit-scrollbar{display:none;}
    .nav-links a{white-space:nowrap;font-size:13px;}
  }

  header.hero{background:linear-gradient(180deg,var(--navy),var(--navy-2));color:#fff;padding:34px 0 28px;}
  h1{margin:0;font-size:clamp(23px,3.4vw,31px);font-weight:800;}
  header.hero p{color:#c9d5e3;font-size:15px;max-width:660px;margin:9px 0 0;}
  header.hero p a{color:#ffd8c4;}

  .jump{position:sticky;top:0;z-index:50;background:rgba(247,248,250,.97);backdrop-filter:blur(6px);
        border-bottom:1px solid var(--line);padding:9px 0;}
  .jump .wrap{display:flex;gap:6px;flex-wrap:wrap;align-items:center;}
  .jump a{font-size:12.5px;font-weight:700;text-decoration:none;border:1px solid var(--line);
          background:#fff;color:var(--ink-soft);border-radius:999px;padding:5px 12px;}
  .jump a:hover{border-color:var(--accent);color:var(--accent-dark);}

  section.dom{padding:26px 0 2px;scroll-margin-top:62px;}
  .dh{display:flex;align-items:center;gap:11px;margin-bottom:14px;flex-wrap:wrap;}
  .dh .n{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;font-weight:700;
         color:#fff;padding:4px 10px;border-radius:7px;}
  .dh h2{margin:0;font-size:17px;font-weight:800;}
  .dh .w{font-size:12px;font-weight:700;color:var(--ink-soft);background:#eef1f6;border-radius:999px;padding:3px 9px;}
  .d1 .n{background:var(--d1);} .d2 .n{background:var(--d2);} .d3 .n{background:var(--d3);}
  .d4 .n{background:var(--d4);} .d5 .n{background:var(--d5);}

  .cols{columns:2;column-gap:16px;}
  @media (max-width:900px){ .cols{columns:1;} }
  .t{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:13px 16px 14px;
     margin:0 0 12px;break-inside:avoid;-webkit-column-break-inside:avoid;}
  .t h3{margin:0 0 8px;font-size:13.5px;font-weight:800;}
  .t h3 b{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--accent-dark);margin-right:6px;}
  .t ul{margin:0;padding:0;list-style:none;}
  .t li{position:relative;font-size:12.8px;line-height:1.45;color:var(--ink-soft);padding:3px 0 3px 14px;}
  .t li:before{content:"";position:absolute;left:2px;top:10px;width:4px;height:4px;border-radius:50%;background:#c3ccd8;}
  .t li.r{color:#8a4a1a;font-weight:600;}
  .t li.r:before{background:var(--accent);}

  footer{padding:28px 0 44px;color:#8b96a5;font-size:12.5px;}
  footer .wrap{border-top:1px solid var(--line);padding-top:18px;}
"""


def build():
    by = collections.OrderedDict()
    for num, title, pts in TASKS:
        by.setdefault(num.split(".")[0], []).append((num, title, pts))

    jump = "".join('<a href="#d%s">Domain %s</a>' % (d, d) for d in by)
    body, npts = [], 0
    for d, tasks in by.items():
        name, wt = DOMAINS[d]
        body.append('\n<section class="dom d%s" id="d%s">\n  <div class="wrap">' % (d, d))
        body.append('    <div class="dh"><span class="n">Domain %s</span><h2>%s</h2>'
                    '<span class="w">%s of the exam</span></div>' % (d, name, wt))
        body.append('    <div class="cols">')
        for num, title, pts in tasks:
            body.append('      <div class="t"><h3><b>%s</b>%s</h3><ul>' % (num, title))
            for p in pts:
                npts += 1
                hard = p.startswith("!")
                body.append('        <li class="%s">%s</li>' % ("r" if hard else "", p.lstrip("!")))
            body.append('      </ul></div>')
        body.append('    </div>\n  </div>\n</section>')

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Revision Sheet | AIP-C01 Guide</title>
<meta name="description" content="One-page revision sheet for the AWS Certified Generative AI Developer (AIP-C01): the key points from all 20 task notes, in plain English.">
<style>%s</style>
</head>
<body>

<nav class="nav">
  <div class="wrap">
    <a class="nav-brand" href="../index.html">AIP-C01 <span>Guide</span></a>
    <ul class="nav-links">
      <li><a href="index.html">Study Notes</a></li>
      <li><a href="cheatsheet.html">Revision Sheet</a></li>
      <li><a href="map.html">The Map</a></li>
      <li><a href="../quiz/exam.html">Mock Exam</a></li>
    </ul>
  </div>
</nav>

<header class="hero">
  <div class="wrap">
    <h1>Revision Sheet</h1>
    <p>%d points from all 20 tasks, in plain English. Orange lines are hard rules and the traps
    that catch people. The full notes are <a href="index.html">here</a>.</p>
  </div>
</header>

<div class="jump"><div class="wrap">%s</div></div>
%s

<footer>
  <div class="wrap">
    <p>Independent, unofficial study resource. Not affiliated with or endorsed by Amazon Web Services, Inc.</p>
  </div>
</footer>

</body>
</html>""" % (CSS, npts, jump, "".join(body))
    open(OUT, "w").write(html)
    print("tasks %d  points %d  %s bytes" % (len(TASKS), npts, format(os.path.getsize(OUT), ",")))


if __name__ == "__main__":
    build()
