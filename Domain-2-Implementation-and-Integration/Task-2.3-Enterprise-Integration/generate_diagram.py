#!/usr/bin/env python3
"""Single source of truth for Task 2.3's architecture diagram.

Emits BOTH:
  Domain-2-.../Task-2.3-.../architecture_diagram.md   (ASCII source in the task folder)
  Website/src/assets/task-2-3-architecture.svg        (rendered figure for the notes page)

The diagram walks one legacy request through the architecture in order, instead of
listing services by layer, so it can show the three things a stacked list cannot:
the XML->JSON->XML round trip, the fork between sync / messaging / bulk ingress,
and the two gates that return an answer without ever invoking a model.
"""
import html, pathlib, textwrap

ROOT = pathlib.Path("/Users/aditya/awsgenai")
MD  = ROOT / "Domain-2-Implementation-and-Integration/Task-2.3-Enterprise-Integration/architecture_diagram.md"
SVG = ROOT / "Website/src/assets/task-2-3-architecture.svg"

TITLE = "TASK 2.3: ONE LEGACY REQUEST, END TO END"

# ---------------------------------------------------------------- flow data
# (phase, [ (title, sub) ... ])  -- "fork" and "gateway" are special-cased
FLOW = [
 ("Origin", [
   ("Legacy core banking system",
    "SOAP · EBCDIC · fixed-width files · JMS/AMQP — holds the records, cannot be rewritten"),
 ]),
 ("Transport — three ways in", "fork"),
 ("Network perimeter", [
   ("Transit Gateway",
    "Dev / Test / Prod isolation; black hole routes guarantee no path can exist from Dev into Prod"),
   ("Network Firewall",
    "stateful rule groups inspect FM-to-legacy traffic; domain filtering blocks exfiltration to unapproved hosts"),
   ("AWS WAF",
    "rate-based rules stop a runaway loop or malicious script before it becomes a seven-figure token bill"),
 ]),
 ("Translation — legacy dialect to JSON", [
   ("API Gateway",
    "mapping template converts XML/SOAP → JSON · regional or edge-optimized · custom domain ai.bank.com"),
   ("Lambda adapter",
    "EBCDIC → UTF-8, fixed-width → JSON · reserved concurrency caps the blast radius, provisioned kills cold starts"),
   ("EventBridge",
    "pattern matching drops events that do not qualify · input transformer normalizes customerId / customer_id / cust.id"),
 ]),
 ("Short-circuit gates — answer before spending a token", [
   ("DynamoDB idempotency check (TTL)",
    "seen this event ID before? webhooks are at-least-once, so duplicates are expected, not exceptional"),
   ("Response cache — API Gateway / ElastiCache / database",
    "has this exact prompt already been answered for anyone?"),
 ]),
 ("The GenAI Gateway", "gateway"),
 ("Private path to the model", [
   ("PrivateLink endpoint policy",
    "never the public internet · bedrock:InvokeModel on claude-* only — no fine-tuning, no deletion"),
 ]),
 ("Orchestration", [
   ("Step Functions · SQS FIFO",
    "Parallel: fraud + balance + limit checks at once · Map: the same check across 1,000 transactions · MessageGroupId = customer-id keeps one customer's steps in order"),
 ]),
 ("Execution — or move the model to the data", [
   ("Amazon Bedrock / Amazon SageMaker",
    "the default path, in-region"),
   ("AWS Outposts · Local Zones · Wavelength",
    "when the data legally cannot leave the premises, the city or the carrier network · filter, anonymize or tokenize before any payload crosses a border"),
 ]),
 ("Return path", [
   ("API Gateway response mapping",
    "JSON → XML/SOAP — back into the exact shape the legacy system already expects"),
   ("Write back",
    "store the response in cache and the event ID in DynamoDB, so the next duplicate exits at the gates above"),
   ("Legacy core banking system",
    "receives XML/SOAP · never modified, never aware a foundation model was involved"),
 ]),
]

FORK = [
 ("Direct Connect", "synchronous, real-time", "dedicated link; BGP policies prioritize inference traffic so bulk sync cannot block it"),
 ("Amazon MQ", "asynchronous messaging", "managed ActiveMQ / RabbitMQ, active/standby — chosen only because the legacy side already speaks JMS/AMQP"),
 ("AWS Glue / AppFlow", "bulk + SaaS sync", "job bookmarks replay only new records · pre-built connectors for Salesforce, ServiceNow, Slack"),
]

GATEWAY = [
 ("Usage plan + API key", "per-team throttle; one team's bug cannot exhaust everyone's capacity"),
 ("Verified Permissions (Cedar)", "department, clearance and business context — the claims the JWT already carries"),
 ("Centralized guardrails", "one safety filter for every team; no application can route around it"),
 ("Model routing, fallback & cost attribution", "swap models without touching a single team's code; bill tokens back per team"),
]

IDENTITY = ("Identity was established out-of-band, at login — not here. "
            "IAM Identity Center federates the corporate directory, so 50,000+ accounts are never re-created, "
            "and the Cognito pre-token Lambda injects department, clearance and region into the JWT. "
            "By the time WAF sees the packet those claims already exist, which is why Cedar can evaluate them at this step.")
DLQ = ("Processing failure routes to a dead-letter queue. Financial events are audit-relevant, "
       "so nothing is ever silently dropped.")
BYPASS = "Returned without invoking a model — zero tokens billed, millisecond latency"
CROSS = [
 ("CloudTrail", "immutable audit trail of every step above"),
 ("KMS multi-region keys", "one decryptable key across 30+ jurisdictions, auto-rotated"),
 ("CloudWatch + X-Ray", "composite alarms; sample 5% normal, 100% of errors"),
 ("Control Tower", "blocks deployments that break data residency"),
]

# ----------------------------------------------------------------- ASCII out
def ascii_doc():
    W = 88
    o = ["=" * W, TITLE.center(W).rstrip(), "=" * W, ""]
    step = 0
    for phase, body in FLOW:
        o.append("[ %s ]" % phase.upper())
        if body == "fork":
            step += 1
            for sfx, (name, mode, sub) in zip("abc", FORK):
                o.append("  +-- (%d%s) %s  --  %s" % (step, sfx, name, mode))
                for ln in textwrap.wrap(sub, W - 12):
                    o.append("  |       %s" % ln)
            o += ["           |", "           v"]
            continue
        if body == "gateway":
            step += 1
            o.append("  +-- (%d) ALL TRAFFIC FUNNELS THROUGH THE GENAI GATEWAY" % step)
            for name, sub in GATEWAY:
                o.append("  |       - %s: %s" % (name, sub))
            for ln in textwrap.wrap("NOTE: " + IDENTITY, W - 12):
                o.append("  |       %s" % ln)
            o += ["           |", "           v"]
            continue
        alt = phase.startswith("Execution")
        if alt:
            step += 1
        for bi, (name, sub) in enumerate(body):
            if not alt:
                step += 1
            if alt and bi:
                o.append("  |   -- or --")
            o.append("  +-- (%s) %s" % ("%d%s" % (step, "ab"[bi]) if alt else step, name))
            for ln in textwrap.wrap(sub, W - 12):
                o.append("  |       %s" % ln)
            if name == "EventBridge":
                for ln in textwrap.wrap("DLQ: " + DLQ, W - 12):
                    o.append("  |       %s" % ln)
            if name.startswith("Response cache"):
                o.append("  |       >>> HIT at either gate: %s" % BYPASS)
                o.append("  |           jumps straight to the response-mapping step below")
        o += ["           |", "           v"]
    while o and o[-1] in ("           |", "           v"):
        o.pop()
    o += ["", "=" * W, "CROSS-CUTTING (applies at every step above)", "=" * W]
    for name, sub in CROSS:
        o.append("  +-- %s: %s" % (name, sub))
    o.append("=" * W)
    return "\n".join(o) + "\n"

MD.write_text(ascii_doc(), encoding="utf-8")
print("wrote %s (%d lines)" % (MD, len(ascii_doc().split("\n"))))

# ------------------------------------------------------------------ SVG out
W, SPINE_X, SPINE_W = 1060, 330, 420
CX   = SPINE_X + SPINE_W // 2
LCOL = (24, 282)            # left callout column  (x, width)
RCOL = (786, 250)           # right bypass rail
GAP  = 48

NARROW, WIDE, UPPER, DIGIT = set("iljtfrI.,:;'|!()[]· "), set("mwMW@"), set(), set("0123456789")
def tw(s, size):
    t = 0.0
    for c in s:
        t += (0.30 if c in NARROW else 0.92 if c in WIDE
              else 0.56 if c in DIGIT else 0.66 if c.isupper() else 0.54)
    return t * size

def wrap(s, size, width):
    out, cur = [], ""
    for word in s.split(" "):
        trial = (cur + " " + word).strip()
        if cur and tw(trial, size) > width:
            out.append(cur); cur = word
        else:
            cur = trial
    if cur: out.append(cur)
    return out

def esc(s): return html.escape(s, quote=False)

o, y = [], 0
def box(x, bw, title, sub, *, num=None, tone="plain", tsize=13, ssize=11):
    """Draw one node; returns its height. Uses/advances nothing - caller owns y."""
    fill, stroke, tcol, scol = {
        "plain": ("#ffffff", "#d7dde8", "#0b1524", "#3a4a5e"),
        "gate":  ("#fff8f4", "#f0c9b4", "#0b1524", "#6b4a3a"),
        "hl":    ("#13304f", "#1b3c68", "#ffffff", "#c9d5e3"),
        "ok":    ("#eef7f1", "#c7e2d1", "#0b1524", "#3a4a5e"),
    }[tone]
    pad = 34 if num else 16
    lines = wrap(sub, ssize, bw - pad - 16) if sub else []
    h = 24 + (len(lines) * 15) + 14
    o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="10" fill="%s" stroke="%s"/>'
             % (x, y, bw, h, fill, stroke))
    if num:
        o.append('<rect x="%d" y="%d" width="26" height="18" rx="5" fill="%s"/>'
                 % (x + 12, y + 13, "#e8622c" if tone == "hl" else "#0f2540"))
        o.append('<text x="%d" y="%d" class="num">%s</text>' % (x + 25, y + 26, num))
    o.append('<text x="%d" y="%d" class="bt" fill="%s" font-size="%s">%s</text>'
             % (x + pad + 6, y + 27, tcol, tsize, esc(title)))
    for i, ln in enumerate(lines):
        o.append('<text x="%d" y="%d" class="bs" fill="%s">%s</text>'
                 % (x + pad + 6, y + 44 + i * 15, scol, esc(ln)))
    return h

def arrow(x, y0, y1, label=None):
    o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#8fa0b6" stroke-width="1.7" marker-end="url(#ah)"/>'
             % (x, y0, x, y1))
    if label:
        o.append('<text x="%d" y="%.1f" class="el" text-anchor="start">%s</text>'
                 % (x + 9, (y0 + y1) / 2 + 3, esc(label)))

def callout(x, bw, head, text):
    lines = wrap(text, 10.5, bw - 26)
    h = 20 + len(lines) * 14 + 12
    o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="9" fill="#f4f6fa" stroke="#e3e7ee"/>'
             % (x, y, bw, h))
    o.append('<text x="%d" y="%d" class="cohead">%s</text>' % (x + 13, y + 20, esc(head)))
    for i, ln in enumerate(lines):
        o.append('<text x="%d" y="%d" class="co">%s</text>' % (x + 13, y + 36 + i * 14, esc(ln)))
    return h

# --- pass: lay out the spine, remembering y of the gate + response-map steps
y = 62
phase_marks, gate_ys, respmap_y = [], [], None
step = 0
for pi, (phase, body) in enumerate(FLOW):
    last_phase = pi == len(FLOW) - 1
    phase_marks.append((y - 11, phase))
    if body == "fork":
        step += 1
        fw, fx = 330, [24, 366, 708]
        hs = []
        for i, (name, mode, sub) in enumerate(FORK):
            yy = y
            hs.append(box(fx[i], fw, name, sub, num="%d%s" % (step, "abc"[i])))
            o.append('<text x="%d" y="%d" class="mode">%s</text>' % (fx[i] + fw - 14, yy + 27, esc(mode)))
            o[-1] = o[-1].replace('class="mode"', 'class="mode" text-anchor="end"')
        y += max(hs)
        arrow(CX, y + 7, y + 25)
        y += GAP
        continue
    if body == "gateway":
        step += 1
        gl = [wrap(s_, 10.5, SPINE_W - 60) for _, s_ in GATEWAY]
        ih = 48 + sum(15 + len(L) * 13 + 8 for L in gl) + 2
        o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="12" fill="#13304f" stroke="#1b3c68"/>'
                 % (SPINE_X, y, SPINE_W, ih))
        o.append('<rect x="%d" y="%d" width="26" height="18" rx="5" fill="#e8622c"/>' % (SPINE_X + 12, y + 13))
        o.append('<text x="%d" y="%d" class="num">%d</text>' % (SPINE_X + 25, y + 26, step))
        o.append('<text x="%d" y="%d" class="bt" fill="#ffffff" font-size="13.5">The GenAI Gateway</text>'
                 % (SPINE_X + 46, y + 27))
        yy = y + 48
        for (n, _), lines in zip(GATEWAY, gl):
            o.append('<circle cx="%d" cy="%.1f" r="2.5" fill="#e8622c"/>' % (SPINE_X + 20, yy - 4))
            o.append('<text x="%d" y="%d" class="gn">%s</text>' % (SPINE_X + 32, yy, esc(n)))
            for j, ln in enumerate(lines):
                o.append('<text x="%d" y="%d" class="gs">%s</text>' % (SPINE_X + 32, yy + 13 + j * 13, esc(ln)))
            yy += 15 + len(lines) * 13 + 8
        ch = callout(LCOL[0], LCOL[1], "Why Cedar can read those claims", IDENTITY)
        y += max(ih, ch)
        arrow(CX, y + 7, y + 25)
        y += GAP
        continue
    alt = phase.startswith("Execution")
    if alt:
        step += 1
    for bi, (name, sub) in enumerate(body):
        if not alt:
            step += 1
        gate = phase.startswith("Short-circuit")
        last = bi == len(body) - 1
        if name == "EventBridge":
            ch = callout(LCOL[0], LCOL[1], "On failure", DLQ)
        h = box(SPINE_X, SPINE_W, name, sub, num=("%d%s" % (step, "ab"[bi])) if alt else str(step),
                tone="gate" if gate else "plain")
        if gate:
            gate_ys.append(y + h / 2)
        if name == "API Gateway response mapping":
            respmap_y = y + h / 2
        y += h
        if not last:
            if alt:
                o.append('<text x="%d" y="%d" class="orlab" text-anchor="middle">or</text>' % (CX, y + 15))
            else:
                arrow(CX, y + 5, y + 13)
            y += 18
    if not last_phase:
        arrow(CX, y + 7, y + 25)
    y += GAP

y -= GAP
bottom = y + 34

# --- right-hand bypass rail
rx, rw = RCOL
r0, r1 = gate_ys[0] - 22, respmap_y
o.insert(0, '<rect x="%d" y="%.1f" width="%d" height="%.1f" rx="12" fill="#eef7f1" stroke="#c7e2d1"/>'
         % (rx, r0, rw, r1 - r0))
for i, ln in enumerate(wrap(BYPASS, 11, rw - 28)):
    o.append('<text x="%d" y="%.1f" class="byp">%s</text>' % (rx + 14, r0 + 26 + i * 15, esc(ln)))
for gy in gate_ys:
    o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#5e9e78" stroke-width="1.6" marker-end="url(#ahg)"/>'
             % (SPINE_X + SPINE_W + 4, gy, rx - 4, gy))
    o.append('<text x="%d" y="%.1f" class="elg">hit</text>' % (SPINE_X + SPINE_W + 14, gy - 6))
o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#5e9e78" stroke-width="1.4" stroke-dasharray="4 4"/>'
         % (rx + rw // 2, r0 + 26 + 15 * len(wrap(BYPASS, 11, rw - 28)), rx + rw // 2, r1 - 10))
o.append('<text x="%d" y="%.1f" class="elg" text-anchor="middle">skips every step in between</text>'
         % (rx + rw // 2, r1 - 22))
o.append('<path d="M %d %.1f L %d %.1f L %d %.1f" fill="none" stroke="#5e9e78" stroke-width="1.6" marker-end="url(#ahg)"/>'
         % (rx + rw // 2, r1 - 10, rx + rw // 2, r1, SPINE_X + SPINE_W + 6, r1))

# --- cross-cutting strip
cw = (W - 48 - 3 * 12) // 4
o.append('<line x1="24" y1="%d" x2="%d" y2="%d" stroke="#e3e7ee"/>' % (bottom - 14, W - 24, bottom - 14))
o.append('<text x="24" y="%d" class="ptitle">Cross-cutting — applies at every step above</text>' % (bottom + 4))
for i, (n, s_) in enumerate(CROSS):
    bx = 24 + i * (cw + 12)
    o.append('<rect x="%d" y="%d" width="%d" height="54" rx="9" fill="#f4f6fa" stroke="#e3e7ee"/>' % (bx, bottom + 16, cw))
    o.append('<text x="%d" y="%d" class="cn">%s</text>' % (bx + 13, bottom + 36, esc(n)))
    for j, ln in enumerate(wrap(s_, 10.5, cw - 26)):
        o.append('<text x="%d" y="%d" class="co">%s</text>' % (bx + 13, bottom + 50 + j * 13, esc(ln)))
H = bottom + 16 + 54 + 24

head = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
        'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif">' % (W, H, W, H),
 '<defs>'
 '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0,1 L9,5 L0,9 z" fill="#8fa0b6"/></marker>'
 '<marker id="ahg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0,1 L9,5 L0,9 z" fill="#5e9e78"/></marker></defs>',
 '<style>'
 '.dtitle{font-size:14.5px;font-weight:800;letter-spacing:.03em;fill:#0f2540;}'
 '.num{font-size:10.5px;font-weight:700;fill:#fff;text-anchor:middle;}'
 '.bt{font-weight:700;}.bs{font-size:11px;}'
 '.gn{font-size:11.5px;font-weight:700;fill:#ffffff;}.gs{font-size:10.5px;fill:#c9d5e3;}'
 '.ptitle{font-size:11px;font-weight:700;letter-spacing:.06em;fill:#16345c;text-transform:uppercase;}'
 '.phase{font-size:10.5px;font-weight:700;letter-spacing:.07em;fill:#8b96a5;text-transform:uppercase;}'
 '.mode{font-size:10px;font-weight:700;fill:#c94f1f;}.orlab{font-size:10.5px;font-weight:700;fill:#8b96a5;letter-spacing:.08em;}'
 '.el{font-size:10px;font-weight:600;fill:#6b7a8d;}.elg{font-size:10px;font-weight:700;fill:#3f8a60;}'
 '.byp{font-size:11px;font-weight:700;fill:#2f6b4c;}'
 '.cohead{font-size:10.5px;font-weight:800;fill:#16345c;}.co{font-size:10.5px;fill:#3a4a5e;}'
 '.cn{font-size:11px;font-weight:700;fill:#0b1524;}'
 '</style>',
 '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H),
 '<text x="24" y="32" class="dtitle">%s</text>' % esc(TITLE),
 '<line x1="24" y1="44" x2="%d" y2="44" stroke="#e3e7ee"/>' % (W - 24)]
for my, ph in phase_marks:
    head.append('<text x="%d" y="%d" class="phase">%s</text>' % (SPINE_X, my, esc(ph)))

SVG.write_text("\n".join(head + o) + "\n</svg>\n", encoding="utf-8")
print("wrote %s (%dx%d, %d steps)" % (SVG, W, H, step))
