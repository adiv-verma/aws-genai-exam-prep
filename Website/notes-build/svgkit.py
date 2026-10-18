# -*- coding: utf-8 -*-
"""SVG helpers matching the house style already used by the domain-map pages."""

BOX_W, BOX_H = 222, 186
GAP = 26
CANVAS_W = 1282

DOM_COLOR = {"1": "#1f4e79", "2": "#6b4c9a", "3": "#1d6f68", "4": "#c94f1f", "5": "#a03453"}


def chip_w(label):
    """Same width formula the existing diagrams use."""
    return round(5.9 * len(label) + 16, 1)


def row_x(n):
    """Left x for each of n boxes, centred on the canvas."""
    total = n * BOX_W + (n - 1) * GAP
    start = (CANVAS_W - total) / 2
    return [round(start + i * (BOX_W + GAP), 1) for i in range(n)]


def band_head(x, y, w, title, sub):
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="27" rx="13.5" fill="#0f2540"/>',
         f'<text x="{x+15}" y="{y+18.5}" font-size="12.5" font-weight="800" fill="#fff" letter-spacing=".04em">{title}</text>']
    if sub:
        o.append(f'<text x="{x+15+len(title)*8.6:.1f}" y="{y+18.5}" font-size="12.5" '
                 f'font-weight="600" fill="#fff" opacity=".85">{sub}</text>')
    return o


def box(x, y, color, title, lines, chips, task, href, linktext, h=BOX_H):
    """One card: coloured top bar, title, up to 3 body lines, chip rows, task pill, link."""
    cx = x + BOX_W / 2
    o = [f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{h}" rx="12" fill="#ffffff" stroke="#d7dee8" stroke-width="1.5"/>',
         f'<rect x="{x+11}" y="{y+1}" width="200" height="4" fill="{color}"/>',
         f'<text x="{cx}" y="{y+29}" text-anchor="middle" font-size="15" font-weight="700" fill="#0b1524">{title}</text>']
    for i, ln in enumerate(lines[:3]):
        o.append(f'<text x="{cx}" y="{y+50+i*17}" text-anchor="middle" font-size="11.8" fill="#5a6a7e">{ln}</text>')

    # chips: pack into rows of total width <= 200, each row centred
    rows, cur, curw = [], [], 0.0
    for c in chips:
        w = chip_w(c)
        if cur and curw + 6 + w > 200:
            rows.append((cur, curw)); cur, curw = [c], w
        else:
            curw = curw + 6 + w if cur else w
            cur.append(c)
    if cur:
        rows.append((cur, curw))

    for ri, (row, roww) in enumerate(rows[:2]):
        cxs = cx - roww / 2
        ry = y + 100 + ri * 20
        for c in row:
            w = chip_w(c)
            o.append(f'<rect x="{cxs:.1f}" y="{ry}" width="{w}" height="16" rx="6" fill="#eef2f7"/>')
            o.append(f'<text x="{cxs+w/2:.1f}" y="{ry+11.5}" text-anchor="middle" font-size="9.6" '
                     f'font-weight="600" fill="#4a5a70">{c}</text>')
            cxs += w + 6

    o.append(f'<rect x="{cx-16}" y="{y+140}" width="32" height="16" rx="8" fill="{color}"/>')
    o.append(f'<text x="{cx}" y="{y+152}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#fff">{task}</text>')
    o.append(f'<line x1="{x+16}" y1="{y+162}" x2="{x+206}" y2="{y+162}" stroke="#d7dee8" stroke-width="1"/>')
    o.append(f'<a href="{href}"><text x="{cx}" y="{y+178}" text-anchor="middle" font-size="11.2" '
             f'font-weight="700" fill="#c94f1f">{linktext} &#8594;</text></a>')
    return o


def arrow(x_end, x_next, y, label=None):
    o = [f'<line x1="{x_end+4}" y1="{y}" x2="{x_next-7}" y2="{y}" stroke="#5a6a7e" stroke-width="1.8" marker-end="url(#a)"/>']
    if label:
        o.append(f'<text x="{(x_end+x_next)/2:.1f}" y="{y-8}" text-anchor="middle" font-size="9.8" '
                 f'font-weight="700" fill="#5a6a7e">{label}</text>')
    return o


def note(x, y, text, w=None, anchor="start"):
    return [f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="11.5" fill="#5a6a7e" font-style="italic">{text}</text>']


def svg_open(h, aria):
    return [f'<svg viewBox="0 0 {CANVAS_W} {h}" role="img" aria-label="{aria}" xmlns="http://www.w3.org/2000/svg">',
            '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
            'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#5a6a7e"/></marker></defs>',
            f'<rect width="{CANVAS_W}" height="{h}" fill="#f7f8fa"/>',
            '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif">']


def svg_close():
    return ['</g>', '</svg>']


# --------------------------------------------------------------------------- #
#  The six concept diagrams. Each draws one mechanism that recurs everywhere,
#  once and properly, so the task pages can point at it instead of re-implying it.
# --------------------------------------------------------------------------- #

def d_rag_path():
    h = 300
    o = svg_open(h, "The RAG request path in five steps. One: query handling, where the user's words are "
        "normalised, spell-corrected, expanded with alternative terminology for up to 23 percent more recall, "
        "and split into parallel sub-queries, from Task 1.5. Two: hybrid retrieval, running dense vector search "
        "for concepts alongside sparse BM25 keyword search for exact codes and proper nouns, because legal and "
        "clinical work needs both. Three: reranking, where a cross-attention model re-orders the top hundred "
        "candidates down to the definitive top ten, with recency and authority weighted in. Four: assembly, "
        "where the chunks are combined with the system prompt and its citation mapping, and guardrails evaluate "
        "the input before the model sees it. Five: verification, where the generated answer is embedded and "
        "compared back against the retrieved chunks, so low similarity reveals fabrication, and confidence "
        "decides whether the answer ships, ships with a disclaimer, or goes to a human. Each box links to the "
        "task notes that own that step.")
    xs = row_x(5)
    y = 58
    steps = [
        ("1", "Handle the query", ["Normalise, fix spelling, expand", "with alternative wording, split", "multi-part questions in parallel."],
         ["expansion +23%", "decomposition"], "1.5", "task-1-5.html#s7", "Notes 1.5 &middot; Section 5"),
        ("1", "Retrieve both ways", ["Dense vectors catch the concept.", "Sparse BM25 catches the exact", "code. Real queries need both."],
         ["hybrid", "BM25", "dense"], "1.5", "task-1-5.html#s6", "Notes 1.5 &middot; Section 4"),
        ("1", "Rerank the shortlist", ["Top 100 cheaply, then cross-", "attention down to the top 10.", "Recency and authority weigh in."],
         ["two-stage", "cross-encoder"], "1.5", "task-1-5.html#s6", "Notes 1.5 &middot; Section 4"),
        ("1", "Assemble and screen", ["Chunks plus system prompt plus", "citation mapping. Guardrails see", "the input before the model does."],
         ["citations", "guardrails"], "1.6", "task-1-6.html#s2", "Notes 1.6 &middot; Section 1"),
        ("3", "Verify before sending", ["Embed the answer, compare it to", "the sources. Low similarity means", "it was invented, not retrieved."],
         ["grounding", "confidence"], "3.1", "task-3-1.html#s3", "Notes 3.1 &middot; Section 3"),
    ]
    for i, (dom, t, lines, chips, task, href, lt) in enumerate(steps):
        o += box(xs[i], y, DOM_COLOR[dom], t, lines, chips, task, href, lt)
        if i < 4:
            o += arrow(xs[i] + BOX_W, xs[i + 1], y + BOX_H / 2)
    o += note(CANVAS_W / 2, 276,
              "Steps 1&ndash;3 are retrieval quality (Task 1.5). Step 4 is control (1.6). Step 5 is the only one that "
              "can tell you the model made it up (3.1).", anchor="middle")
    return numeric("\n".join(o + svg_close()))


def d_ingest():
    h = 300
    o = svg_open(h, "The ingestion pipeline that has to happen before any retrieval works, in five stages. "
        "One: chunk the document, choosing fixed-size, structure-aware, hierarchical parent-child or semantic "
        "per document type rather than uniformly, with about ten percent overlap so sentences spanning a "
        "boundary survive. Two: attach metadata now, because adding jurisdiction, date or sensitivity after "
        "vectors are stored requires a full and costly re-ingestion. Three: redact personal data and then "
        "embed, using the same embedding model you will use at query time, because switching models shifts the "
        "whole vector space and breaks every stored similarity. Four: build the index, choosing between HNSW, "
        "IVF, LSH and product quantization against your own dataset, and tuning the parameters that trade "
        "memory and build time against recall. Five: keep operating it, because indexes fragment, embeddings "
        "drift as language moves on, and a snapshot restores in minutes where re-embedding the corpus takes "
        "hours and a full inference bill.")
    xs = row_x(5)
    y = 58
    steps = [
        ("1", "Cut it up", ["Per document type, not one rule", "for everything. Keep ~10% overlap", "so split sentences survive."],
         ["4 strategies", "overlap"], "1.5", "task-1-5.html#s3", "Notes 1.5 &middot; Section 1"),
        ("1", "Tag it now", ["Jurisdiction, date, sensitivity.", "Adding metadata after storage", "means re-ingesting everything."],
         ["taxonomy", "pre-filter"], "1.4", "task-1-4.html#s2", "Notes 1.4 &middot; Step 2"),
        ("3", "Redact, then embed", ["Scrub PII first &mdash; once it is in the", "coordinates it cannot come out.", "Then embed, once, consistently."],
         ["same model rule", "PII"], "3.2", "task-3-2.html#s3", "Notes 3.2 &middot; Part 3"),
        ("4", "Build the index", ["HNSW, IVF, LSH or PQ &mdash; chosen", "by benchmark, not reputation.", "Tune recall against memory."],
         ["HNSW", "ef_search", "recall"], "4.2", "task-4-2.html#t2", "Notes 4.2 &middot; Topic 2"),
        ("4", "Keep it healthy", ["Indexes fragment, embeddings", "drift. Snapshot restores in", "minutes; re-embedding takes days."],
         ["fragmentation", "snapshots"], "4.3", "task-4-3.html#s5", "Notes 4.3 &middot; Section 5"),
    ]
    for i, (dom, t, lines, chips, task, href, lt) in enumerate(steps):
        o += box(xs[i], y, DOM_COLOR[dom], t, lines, chips, task, href, lt)
        if i < 4:
            o += arrow(xs[i] + BOX_W, xs[i + 1], y + BOX_H / 2)
    o += note(CANVAS_W / 2, 276,
              "Two of these are one-way doors: metadata attached too late, and PII embedded before redaction. "
              "Both cost a full corpus rebuild.", anchor="middle")
    return numeric("\n".join(o + svg_close()))


def d_guardrail():
    h = 510
    o = svg_open(h, "Defense in depth around a model, as two bands. The first band runs before the model and is "
        "ordered deliberately from cheapest to most expensive, so a malicious request is killed before it costs "
        "a token: AWS WAF and rate limiting, which is a security control because it stops an attacker grinding "
        "through thousands of prompt variations; then Lambda regex sanitisation for SQL injection and cross-site "
        "scripting, which is pure pattern matching and needs no API call; then Amazon Comprehend for sentiment, "
        "PII detection and risk scoring, which is fast and cheap and lets the workflow branch by severity; then "
        "Bedrock Guardrails for prompt injection, denied topics and PII masking, which sit outside both the "
        "model and the prompt and so cannot be talked out of their job; and only then the model itself, the most "
        "expensive step. The second band runs after the model: Guardrails again on the output in either block "
        "mode or filtered-alternative mode, then a post-processing Lambda for the exact business rules "
        "Guardrails cannot know, such as masking all but the last four digits with a Luhn check, then API "
        "Gateway stripping internal metadata, then monitoring in CloudWatch and Security Hub that tracks which "
        "layer caught what. The closing note explains the blind spots: WAF cannot read plain-English attacks, "
        "Comprehend misses zero-days, Guardrails cannot verify account ownership, and post-processing is too "
        "late to stop the bill.")
    o += band_head(34, 16, 560, "BEFORE THE MODEL", "Cheapest filter first  &middot;  Task 3.1")
    xs = row_x(5)
    y = 58
    pre = [
        ("3", "WAF &amp; rate limits", ["Known web payloads, geo rules,", "and rate caps that stop someone", "brute-forcing prompt variants."],
         ["near-free", "security control"], "3.1", "task-3-1.html#s4", "Notes 3.1 &middot; Section 4"),
        ("3", "Lambda regex", ["SQLi, XSS, JSON structure.", "Pure pattern matching, no API", "call, so it runs first."],
         ["very cheap"], "3.1", "task-3-1.html#s1", "Notes 3.1 &middot; Section 1"),
        ("3", "Comprehend", ["Sentiment, PII, risk category.", "Cheap enough to run on every", "request and branch on severity."],
         ["cheap", "risk scoring"], "3.1", "task-3-1.html#s1", "Notes 3.1 &middot; Section 1"),
        ("3", "Guardrails", ["Injection, denied topics, PII.", "Outside the model and outside", "the prompt &mdash; so unbypassable."],
         ["moderate", "LOW = strictest"], "3.1", "task-3-1.html#s2", "Notes 3.1 &middot; Section 2"),
        ("1", "The model", ["The most expensive step in the", "chain. Everything above exists", "to avoid paying for it twice."],
         ["most expensive"], "1.1", "task-1-1.html#s4", "Notes 1.1 &middot; Section 4"),
    ]
    for i, (dom, t, lines, chips, task, href, lt) in enumerate(pre):
        o += box(xs[i], y, DOM_COLOR[dom], t, lines, chips, task, href, lt)
        if i < 4:
            o += arrow(xs[i] + BOX_W, xs[i + 1], y + BOX_H / 2)

    o += band_head(34, 268, 560, "AFTER THE MODEL", "Nothing leaves unchecked  &middot;  Tasks 3.1, 3.2")
    xs2 = row_x(4)
    y2 = 310
    post = [
        ("3", "Guardrails again", ["Block the whole answer, or strip", "just the bad part and keep the", "rest. Two different modes."],
         ["block", "filtered"], "3.1", "task-3-1.html#s2", "Notes 3.1 &middot; Section 2"),
        ("3", "Post-process Lambda", ["Guardrails writes [PII].", "Compliance wants ****1234 with", "a Luhn check. Code does that."],
         ["exact rules", "fail-safe"], "3.1", "task-3-1.html#s2", "Notes 3.1 &middot; Section 2"),
        ("2", "Strip at the edge", ["API Gateway removes internal", "metadata and system details", "before the payload ships."],
         ["response filter"], "2.3", "task-2-3.html#s3", "Notes 2.3 &middot; Section 2"),
        ("3", "Watch which layer caught it", ["Lots of bad input reaching the", "last layer means the early ones", "are misconfigured."],
         ["Security Hub", "per-layer"], "3.1", "task-3-1.html#s4", "Notes 3.1 &middot; Section 4"),
    ]
    for i, (dom, t, lines, chips, task, href, lt) in enumerate(post):
        o += box(xs2[i], y2, DOM_COLOR[dom], t, lines, chips, task, href, lt)
        if i < 3:
            o += arrow(xs2[i] + BOX_W, xs2[i + 1], y2 + BOX_H / 2)
    o += note(CANVAS_W / 2, 488,
              "Every layer has a blind spot: WAF cannot read &ldquo;ignore previous rules&rdquo;, Comprehend misses zero-days, "
              "Guardrails cannot check who owns the account, post-processing is too late to stop the bill.", anchor="middle")
    return numeric("\n".join(o + svg_close()))


def d_cascade():
    h = 510
    o = svg_open(h, "How a request chooses a model, and then who signs off, as two bands. The first band is the "
        "routing ladder: a lightweight classifier or config flag reads the request's complexity, token count, "
        "language and domain, costing milliseconds rather than a model call; the cheap model attempts it first "
        "and answers roughly eighty percent of ordinary queries for a fraction of the price; a confidence gate "
        "between zero point seven and zero point nine decides whether that answer stands; and on escalation the "
        "large model receives the partial findings from the first attempt so it does not restart from nothing, "
        "at the cost of two API calls and more latency for that request, which is why cascading only pays when "
        "most queries really are simple. The second band is the human ladder keyed to the same confidence "
        "number: above zero point nine it is fully automated, between zero point seven and zero point nine it "
        "executes with asynchronous human review, below zero point seven it waits for synchronous approval, "
        "held open by a Step Functions wait token with a twenty-four hour timeout rather than being terminated. "
        "The closing note warns that the same numbers gate completely different things across tasks.")
    o += band_head(34, 16, 580, "CHOOSING A MODEL", "Cheapest first  &middot;  Tasks 4.1, 2.2, 2.4")
    xs = row_x(4)
    y = 58
    lad = [
        ("4", "Read the request", ["A classifier or a config flag:", "complexity, tokens, language,", "domain. Milliseconds, not a call."],
         ["tiered routing", "AppConfig"], "4.1", "task-4-1.html#s2", "Notes 4.1 &middot; Section 2"),
        ("4", "Try cheap first", ["The small model answers ~80% of", "ordinary queries for a fraction", "of the price. Quality bar first."],
         ["up to 80% saved"], "4.1", "task-4-1.html#s2", "Notes 4.1 &middot; Section 2"),
        ("2", "Gate on confidence", ["Below 0.7&ndash;0.9 the answer does not", "stand. Above it, return now and", "never pay for the big model."],
         ["0.7 &ndash; 0.9"], "2.4", "task-2-4.html#s4", "Notes 2.4 &middot; Section 4"),
        ("2", "Escalate with context", ["The large model gets the partial", "findings, not a blank slate. Two", "calls, so more latency, not less."],
         ["metadata passing"], "2.2", "task-2-2.html#s3", "Notes 2.2 &middot; Section 3"),
    ]
    for i, (dom, t, lines, chips, task, href, lt) in enumerate(lad):
        o += box(xs[i], y, DOM_COLOR[dom], t, lines, chips, task, href, lt)
        if i < 3:
            o += arrow(xs[i] + BOX_W, xs[i + 1], y + BOX_H / 2,
                       label=["", "low conf.", "escalate"][i] or None)

    o += band_head(34, 268, 580, "WHO SIGNS IT OFF", "Same number, different gate  &middot;  Task 2.1")
    xs2 = row_x(3)
    y2 = 310
    hum = [
        ("2", "Above 0.9", ["Fully automated. Nobody looks", "at it, and nothing waits for a", "person to come back from lunch."],
         ["automated"], "2.1", "task-2-1.html#s6", "Notes 2.1 &middot; Section 6"),
        ("2", "0.7 to 0.9", ["It acts, then a human reviews it", "afterwards. Speed kept, with a", "record somebody actually reads."],
         ["async review"], "2.1", "task-2-1.html#s6", "Notes 2.1 &middot; Section 6"),
        ("2", "Below 0.7", ["Nothing happens until a person", "approves. A wait token holds the", "state open, with a 24h timeout."],
         ["wait token", "sync approval"], "2.1", "task-2-1.html#s6", "Notes 2.1 &middot; Section 6"),
    ]
    for i, (dom, t, lines, chips, task, href, lt) in enumerate(hum):
        o += box(xs2[i], y2, DOM_COLOR[dom], t, lines, chips, task, href, lt)
        if i < 2:
            o += arrow(xs2[i] + BOX_W, xs2[i + 1], y2 + BOX_H / 2)
    o += note(CANVAS_W / 2, 488,
              "The band 0.7&ndash;0.9 appears in five tasks gating five different things &mdash; a bigger model, a human "
              "reviewer, a clarifying question, a disclaimer, a blocked response. The number repeats; what it "
              "controls does not.", anchor="middle")
    return numeric("\n".join(o + svg_close()))


def d_resilience():
    h = 300
    o = svg_open(h, "What happens when a model call fails, as five steps. One: classify the error, because a "
        "generic API failure tells you nothing. A 429 means capacity is briefly gone and will return, a 5xx "
        "means the provider broke, and a 4xx is your own malformed request which will fail identically forever "
        "and must never be retried. Two: back off with jitter. Waits of one hundred, two hundred, four hundred "
        "and eight hundred milliseconds with random variance, capped at twenty seconds, where the randomness "
        "exists to stop thousands of clients failing on the same millisecond and reconnecting in lockstep. "
        "Three: trip the circuit breaker when half of a ten-request window fails, then stop calling entirely "
        "for thirty to sixty seconds and re-open at ten to twenty percent of traffic to test recovery before "
        "committing. Four: degrade in steps rather than failing, from the specialised model, to a general model "
        "with specialised prompts, to retrieval over verified internal documents, to a deterministic rule-based "
        "system for anything life-critical. Five: shed load deliberately, dropping or delaying low-priority "
        "traffic so emergency requests keep their capacity. The closing note points out that forty percent of "
        "failures in the real case never reached the model at all.")
    xs = row_x(5)
    y = 58
    steps = [
        ("2", "Name the failure", ["429 means wait. 5xx means they", "broke. 4xx means you did &mdash; and", "will fail the same way forever."],
         ["429 / 5xx / 4xx"], "2.5", "task-2-5.html#s1", "Notes 2.5 &middot; Section 1"),
        ("2", "Back off, with jitter", ["100, 200, 400, 800 ms, capped at", "20 s. Randomness stops everyone", "reconnecting on the same tick."],
         ["backoff", "jitter", "cap"], "2.4", "task-2-4.html#s3", "Notes 2.4 &middot; Section 3"),
        ("2", "Trip the breaker", ["Half of ten requests failing and", "it stops calling. Re-opens at", "10&ndash;20% to test the water."],
         ["50% / 10 reqs", "half-open"], "2.4", "task-2-4.html#s3", "Notes 2.4 &middot; Section 3"),
        ("2", "Degrade in steps", ["Specialist model, then general", "plus prompts, then RAG over", "verified docs, then plain rules."],
         ["fallback chain"], "2.4", "task-2-4.html#s3", "Notes 2.4 &middot; Section 3"),
        ("5", "Shed the cheap stuff", ["Drop or delay low-priority work", "on purpose, so emergency traffic", "keeps the capacity it needs."],
         ["load shedding", "priority"], "5.2", "task-5-2.html#s2", "Notes 5.2 &middot; Section 2"),
    ]
    for i, (dom, t, lines, chips, task, href, lt) in enumerate(steps):
        o += box(xs[i], y, DOM_COLOR[dom], t, lines, chips, task, href, lt)
        if i < 4:
            o += arrow(xs[i] + BOX_W, xs[i + 1], y + BOX_H / 2)
    o += note(CANVAS_W / 2, 276,
              "In the Task 5.2 case, 40% of &ldquo;API failures&rdquo; were malformed client payloads that never reached "
              "Bedrock. A pre-call validation Lambda removed them outright.", anchor="middle")
    return numeric("\n".join(o + svg_close()))


def d_evalloop():
    h = 330
    o = svg_open(h, "The loop that decides whether a change ships, in five steps plus a feedback arrow. One: fix "
        "a golden dataset of known-good question and answer pairs, including edge cases, adversarial inputs and "
        "regulatory boundaries, and version it together with the prompts and the weights, because changing the "
        "dataset makes two runs non-comparable. Two: score the candidate across independent dimensions, letting "
        "a second and stronger model judge against a written rubric, never the same model judging itself. "
        "Three: let the gate decide. Below threshold the pipeline blocks its own release, which removes human "
        "discretion from the decision at exactly the moment discretion is least reliable. Four: roll out by "
        "degrees, five to ten percent of live traffic to the candidate, with significance testing before "
        "anything widens. Five: keep watching, because a model that passed can still drift as the world moves, "
        "and a bias or quality alarm shifts traffic back to the last known-good version automatically. The "
        "feedback arrow returns production failures to the golden dataset, so the suite grows from real "
        "incidents rather than imagination.")
    xs = row_x(5)
    y = 58
    steps = [
        ("1", "Fix the dataset", ["Known-good pairs, edge cases,", "adversarial inputs. Versioned", "with the prompt and the weights."],
         ["golden dataset", "joint version"], "1.6", "task-1-6.html#s5", "Notes 1.6 &middot; Section 4"),
        ("5", "Score it properly", ["Independent dimensions, and a", "stronger model marking against", "a rubric. Never itself."],
         ["4 dimensions", "LLM-as-judge"], "5.1", "task-5-1.html#s1", "Notes 5.1 &middot; Section 1"),
        ("5", "Let the gate decide", ["Below threshold, the pipeline", "blocks its own release. No human", "discretion at the worst moment."],
         ["quality gate", "RELEASE BLOCKED"], "5.1", "task-5-1.html#s4", "Notes 5.1 &middot; Section 4"),
        ("5", "Roll out by degrees", ["5&ndash;10% of live traffic, then", "significance testing before it", "widens. Canary, not a big bang."],
         ["canary", "A/B"], "5.1", "task-5-1.html#s2", "Notes 5.1 &middot; Section 2"),
        ("3", "Keep watching", ["Passing once is not passing", "forever. A drift alarm shifts", "traffic back on its own."],
         ["drift", "auto-rollback"], "3.3", "task-3-3.html#s4", "Notes 3.3 &middot; Step 4"),
    ]
    for i, (dom, t, lines, chips, task, href, lt) in enumerate(steps):
        o += box(xs[i], y, DOM_COLOR[dom], t, lines, chips, task, href, lt)
        if i < 4:
            o += arrow(xs[i] + BOX_W, xs[i + 1], y + BOX_H / 2)
    # feedback arrow, right box back to left box
    x0, x4 = xs[0], xs[4]
    o += [f'<path d="M {x4+BOX_W/2:.1f} 250 L {x4+BOX_W/2:.1f} 278 L {x0+BOX_W/2:.1f} 278 L {x0+BOX_W/2:.1f} 252" '
          f'fill="none" stroke="#5a6a7e" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#a)"/>',
          f'<text x="{CANVAS_W/2:.1f}" y="294" text-anchor="middle" font-size="11.5" font-weight="700" fill="#5a6a7e">'
          'What broke in production becomes the next test case</text>']
    o += note(CANVAS_W / 2, 316,
              "Change the evaluation dataset and v7 against v8 stops meaning anything. That is why prompts, "
              "weights and test data are versioned as one snapshot.", anchor="middle")
    return numeric("\n".join(o + svg_close()))


DIAGRAMS = {
    "rag-path":   ("How a question becomes a grounded answer", "The five steps every RAG request goes through, and which task owns each one.", d_rag_path),
    "ingest":     ("What has to happen before any of that works", "Chunk, tag, embed, index, maintain &mdash; with two one-way doors in it.", d_ingest),
    "cascade":    ("Which model answers, and who signs it off", "One confidence number, two completely different ladders hanging off it.", d_cascade),
    "guardrail":  ("The checks either side of the model", "Ordered cheapest-first, because the model is the expensive part.", d_guardrail),
    "evalloop":   ("The loop that decides whether it ships", "Golden set, judge, gate, canary, drift watch &mdash; then back to the golden set.", d_evalloop),
    "resilience": ("What happens on a bad day", "Classify, back off, trip, degrade, shed &mdash; in that order.", d_resilience),
}


# Match the house convention: numeric entities only inside SVG, so the markup stays
# valid XML even if a diagram is ever lifted out of the page.
_NUM = {
    "&mdash;": "&#8212;", "&ndash;": "&#8211;", "&rarr;": "&#8594;", "&larr;": "&#8592;",
    "&ldquo;": "&#8220;", "&rdquo;": "&#8221;", "&lsquo;": "&#8216;", "&rsquo;": "&#8217;",
    "&hellip;": "&#8230;", "&nbsp;": "&#160;", "&plusmn;": "&#177;", "&times;": "&#215;",
    "&le;": "&#8804;", "&ge;": "&#8805;", "&epsilon;": "&#949;", "&middot;": "&#183;",
}


def numeric(s):
    for k, v in _NUM.items():
        s = s.replace(k, v)
    return s
