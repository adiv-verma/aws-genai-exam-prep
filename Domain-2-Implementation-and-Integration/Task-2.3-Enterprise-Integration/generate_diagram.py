#!/usr/bin/env python3
"""Single source of truth for Task 2.3's architecture diagram.

Emits BOTH the ASCII architecture_diagram.md (task folder) and the site SVG.

Three callers enter by three different front doors - and the endpoint type is
chosen per caller, not per workload, which is the whole point of the top band.
They converge on one shared path: filter -> short-circuit gates -> GenAI Gateway
-> model -> back out in whatever shape the caller speaks.
"""
import html, pathlib, textwrap

ROOT = pathlib.Path("/Users/aditya/awsgenai")
MD   = ROOT / "Domain-2-Implementation-and-Integration/Task-2.3-Enterprise-Integration/architecture_diagram.md"
SVG  = ROOT / "Website/src/assets/task-2-3-architecture.svg"

TITLE = "TASK 2.3: THREE CALLERS, ONE GOVERNED PATH TO THE MODEL"

# ------------------------------------------------------------------- lanes
# (letter, name, mode, [(title, sub, [bullets])])
LANES = [
 ("A", "Consumer & workforce clients", "public internet", [
   ("Web · mobile · branch staff",
    "Cognito user pools hold the external consumer identities; Amplify DataStore keeps branch staff working offline and resolves conflicts on reconnect", []),
   ("AWS WAF",
    "rate-based, geo-match and SQL injection rules — a malicious script or an infinite loop is capped before it becomes a token bill", []),
   ("API Gateway — EDGE-OPTIMIZED  ·  AppSync",
    "CloudFront fronts the API because these users are spread across 30+ countries · custom domain ai.bank.com · AppSync VTL resolvers map GraphQL straight to a model payload", []),
 ]),
 ("B", "Legacy core systems", "private network", [
   ("Legacy core banking system",
    "SOAP · EBCDIC · fixed-width files · JMS/AMQP — holds the records, cannot be rewritten", []),
   ("Private transport — pick one", "", [
     "Direct Connect — synchronous; BGP policies prioritize inference so bulk sync cannot block it",
     "Amazon MQ — chosen only because the legacy side already speaks JMS/AMQP",
     "AWS Glue · AppFlow — bulk and SaaS sync; job bookmarks replay only new records",
   ]),
   ("Transit Gateway · Network Firewall",
    "black hole routes guarantee no path from Dev into Prod · stateful inspection and domain filtering stop exfiltration to unapproved hosts", []),
   ("API Gateway — REGIONAL",
    "the caller is already inside the network, so CloudFront would add a hop and buy nothing · mapping template converts XML/SOAP → JSON", []),
   ("Lambda adapter",
    "EBCDIC → UTF-8, fixed-width → JSON · reserved concurrency caps the blast radius, provisioned kills cold starts", []),
 ]),
 ("C", "External webhooks", "public endpoint", [
   ("Partner & SaaS callbacks",
    "loan approvals, settlement notices — delivered at-least-once, so duplicates are guaranteed, not exceptional", []),
   ("AWS WAF",
    "rate-based rules; a looping sender cannot run up the bill", []),
   ("API Gateway — REGIONAL",
    "a webhook handler has no global audience to serve — the sender is a machine, not a travelling user", []),
 ]),
]

ENDPOINT_RULE = ("Endpoint type follows the caller, not the workload.  "
                 "EDGE-OPTIMIZED puts a CloudFront distribution in front when users are scattered worldwide (lane A).  "
                 "REGIONAL is right when the caller is already in-region — a legacy system on Direct Connect, or a webhook sender (lanes B and C).")

# ------------------------------------------------------------------- spine
SPINE = [
 ("Normalize", [
   ("EventBridge",
    "pattern matching drops events that do not qualify · input transformer folds three callers' payloads — customerId, customer_id, cust.id — into one shape, so nothing downstream parses three dialects"),
 ]),
 ("Short-circuit gates — answer before spending a token", [
   ("DynamoDB idempotency check (TTL)",
    "seen this event ID before? this is what makes lane C's at-least-once delivery safe — a duplicate returns the stored result instead of re-invoking and double-billing"),
   ("Response cache — API Gateway / ElastiCache / database",
    "has this exact prompt already been answered for anyone? invalidated by TTL, by an EventBridge event on data change, or write-through"),
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
   ("Amazon Bedrock / Amazon SageMaker", "the default path, in-region"),
   ("AWS Outposts · Local Zones · Wavelength",
    "when the data legally cannot leave the premises, the city or the carrier network · filter, anonymize or tokenize before any payload crosses a border"),
 ]),
 ("Return path — each caller gets its own shape back", [
   ("API Gateway response mapping",
    "lane B gets JSON → XML/SOAP, the exact shape it already expects · lanes A and C get JSON unchanged"),
   ("Write back",
    "store the response in cache and the event ID in DynamoDB, so the next duplicate exits at the gates above"),
   ("Back to the caller",
    "the legacy core is never modified and never aware a foundation model was involved"),
 ]),
]

GATEWAY = [
 ("Usage plan + API key per team", "Team A, Team B, Team C each get their own throttle; one team's runaway bug cannot exhaust everyone's capacity"),
 ("Verified Permissions (Cedar)", "department, clearance and business context — the claims the JWT already carries"),
 ("Centralized guardrails", "one safety filter for every caller and every team; no application can route around it"),
 ("Model routing, fallback & cost attribution", "swap models without touching a single team's code; bill tokens back per team"),
]

IDENTITY = ("Identity was established out-of-band, before the request — not here. IAM Identity Center federates the "
            "corporate directory for workforce users, so 50,000+ accounts are never re-created, and in lane A the "
            "Cognito pre-token Lambda injects department, clearance and region into the JWT. By the time WAF sees "
            "the packet those claims already exist, which is why Cedar can evaluate them at this step.")
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
    o = ["=" * W, TITLE.center(W).rstrip(), "=" * W, "",
         "THREE WAYS IN - the lanes run in parallel; each caller gets the endpoint type that suits it.", ""]
    for letter, name, mode, boxes in LANES:
        o.append("[ LANE %s - %s  (%s) ]" % (letter, name.upper(), mode))
        for i, (t, sub, bullets) in enumerate(boxes):
            o.append("  +-- (%s%d) %s" % (letter, i + 1, t))
            for ln in textwrap.wrap(sub, W - 12):
                o.append("  |       %s" % ln)
            for b in bullets:
                wrapped = textwrap.wrap(b, W - 16)
                o.append("  |       - %s" % wrapped[0])
                for ln in wrapped[1:]:
                    o.append("  |         %s" % ln)
            if i < len(boxes) - 1:
                o.append("  |")
        o.append("")
    o.append("*" * W)
    for ln in textwrap.wrap(ENDPOINT_RULE, W - 4):
        o.append("  " + ln)
    o.append("*" * W)
    o += ["", "            \\        |        /", "             v       v       v", ""]

    step = 0
    for phase, body in SPINE:
        o.append("[ %s ]" % phase.upper())
        if body == "gateway":
            step += 1
            o.append("  +-- (%d) ALL THREE LANES FUNNEL THROUGH THE GENAI GATEWAY" % step)
            for n, sub in GATEWAY:
                for j, ln in enumerate(textwrap.wrap("%s: %s" % (n, sub), W - 16)):
                    o.append("  |       %s%s" % ("- " if j == 0 else "  ", ln))
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
                o.append("  |           skips every step in between, straight to response mapping")
        if phase != SPINE[-1][0]:
            o += ["           |", "           v"]
    o += ["", "=" * W, "CROSS-CUTTING (applies at every step above)", "=" * W]
    for name, sub in CROSS:
        o.append("  +-- %s: %s" % (name, sub))
    o.append("=" * W)
    return "\n".join(o) + "\n"

MD.write_text(ascii_doc(), encoding="utf-8")
print("wrote %s (%d lines)" % (MD, len(ascii_doc().split("\n"))))

# ------------------------------------------------------------------ SVG out
W = 1060
LANE_X, LANE_W = [24, 370, 716], 320
CX = LANE_X[1] + LANE_W // 2                     # 530 - middle lane doubles as the spine
SPINE_X, SPINE_W = CX - 215, 430
GAP = 48

NARROW, WIDE, DIGIT = set("iljtfrI.,:;'|!()[]· "), set("mwMW@"), set("0123456789")
def tw(s, size):
    return sum(0.30 if c in NARROW else 0.92 if c in WIDE else 0.56 if c in DIGIT
               else 0.66 if c.isupper() else 0.54 for c in s) * size

def wrap(s, size, width):
    out, cur = [], ""
    for word in s.split(" "):
        t = (cur + " " + word).strip()
        if cur and tw(t, size) > width:
            out.append(cur); cur = word
        else:
            cur = t
    if cur: out.append(cur)
    return out

def esc(s): return html.escape(s, quote=False)

o = []
TONES = {"plain": ("#ffffff", "#d7dde8", "#0b1524", "#3a4a5e"),
         "gate":  ("#fff8f4", "#f0c9b4", "#0b1524", "#6b4a3a"),
         "edge":  ("#f3f7fd", "#c6d8ef", "#0b1524", "#3a4a5e")}

def box(x, bw, yy, title, sub, bullets=(), *, num=None, tone="plain", tsize=12.5, ssize=10.5):
    fill, stroke, tcol, scol = TONES[tone]
    pad = 36 if num else 14
    lines = wrap(sub, ssize, bw - pad - 14) if sub else []
    bl = [wrap(b, ssize, bw - pad - 26) for b in bullets]
    h = 24 + len(lines) * 14 + sum(len(L) * 14 + 4 for L in bl) + 14
    o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="10" fill="%s" stroke="%s"/>'
             % (x, yy, bw, h, fill, stroke))
    if num:
        nw = 30 if len(str(num)) > 2 else 26
        o.append('<rect x="%d" y="%d" width="%d" height="18" rx="5" fill="#0f2540"/>' % (x + 11, yy + 12, nw))
        o.append('<text x="%.1f" y="%d" class="num">%s</text>' % (x + 11 + nw / 2, yy + 25, esc(str(num))))
    o.append('<text x="%d" y="%d" class="bt" fill="%s" font-size="%s">%s</text>'
             % (x + pad + 4, yy + 26, tcol, tsize, esc(title)))
    ty = yy + 42
    for ln in lines:
        o.append('<text x="%d" y="%d" class="bs" fill="%s">%s</text>' % (x + pad + 4, ty, scol, esc(ln)))
        ty += 14
    for L in bl:
        o.append('<circle cx="%d" cy="%.1f" r="2" fill="#8fa0b6"/>' % (x + pad + 8, ty - 4))
        for k, ln in enumerate(L):
            o.append('<text x="%d" y="%d" class="bs" fill="%s">%s</text>' % (x + pad + 18, ty, scol, esc(ln)))
            ty += 14
        ty += 4
    return h

def arrow(x, y0, y1):
    o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#8fa0b6" stroke-width="1.7" marker-end="url(#ah)"/>'
             % (x, y0, x, y1))

def callout(x, bw, yy, head, text):
    lines = wrap(text, 10.5, bw - 26)
    h = 20 + len(lines) * 14 + 12
    o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="9" fill="#f4f6fa" stroke="#e3e7ee"/>' % (x, yy, bw, h))
    o.append('<text x="%d" y="%d" class="cohead">%s</text>' % (x + 13, yy + 20, esc(head)))
    for i, ln in enumerate(lines):
        o.append('<text x="%d" y="%d" class="co">%s</text>' % (x + 13, yy + 36 + i * 14, esc(ln)))
    return h

# ---- lane band -----------------------------------------------------------
LANE_TOP = 96
o.append('<text x="24" y="76" class="band">Three ways in — the lanes run in parallel</text>')
lane_bottom = []
for li, (letter, name, mode, boxes) in enumerate(LANES):
    x = LANE_X[li]
    o.append('<rect x="%d" y="%d" width="%d" height="30" rx="8" fill="#0f2540"/>' % (x, LANE_TOP, LANE_W))
    o.append('<text x="%d" y="%d" class="lname">%s &#183; %s</text>' % (x + 13, LANE_TOP + 20, letter, esc(name)))
    o.append('<text x="%d" y="%d" class="lmode" text-anchor="end">%s</text>' % (x + LANE_W - 13, LANE_TOP + 20, esc(mode)))
    yy = LANE_TOP + 30 + 14
    for bi, (t, sub, bullets) in enumerate(boxes):
        tone = "edge" if "API Gateway" in t else "plain"
        h = box(x, LANE_W, yy, t, sub, bullets, num="%s%d" % (letter, bi + 1), tone=tone)
        yy += h
        if bi < len(boxes) - 1:
            arrow(x + LANE_W // 2, yy + 4, yy + 14)
            yy += 18
    lane_bottom.append(yy)

# ---- endpoint rule + convergence ----------------------------------------
y = max(lane_bottom) + 26
rl = wrap(ENDPOINT_RULE, 11, W - 90)
rh = 22 + len(rl) * 15 + 12
o.append('<rect x="24" y="%d" width="%d" height="%d" rx="10" fill="#fff8f4" stroke="#e8a983"/>' % (y, W - 48, rh))
o.append('<rect x="24" y="%d" width="5" height="%d" rx="2.5" fill="#e8622c"/>' % (y, rh))
o.append('<text x="44" y="%d" class="rulehead">The answer to “regional or edge-optimized?”</text>' % (y + 20))
for i, ln in enumerate(rl):
    o.append('<text x="44" y="%d" class="rule">%s</text>' % (y + 38 + i * 15, esc(ln)))
for li in range(3):
    lx = LANE_X[li] + LANE_W // 2
    o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#8fa0b6" stroke-width="1.7"/>'
             % (lx, lane_bottom[li] + 4, lx, y - 14))
    if li != 1:
        o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#8fa0b6" stroke-width="1.7"/>' % (lx, y - 14, CX, y - 14))
o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#8fa0b6" stroke-width="1.7" marker-end="url(#ah)"/>'
         % (CX, y - 14, CX, y - 4))
o.append('<text x="%d" y="%d" class="conv" text-anchor="middle">all three converge</text>'
         % ((CX + LANE_X[2] + LANE_W // 2) // 2, y - 20))
y += rh
arrow(CX, y + 7, y + 25)
y += GAP

# ---- converged spine -----------------------------------------------------
phase_marks, gate_ys, respmap_y = [], [], None
step = 0
for pi, (phase, body) in enumerate(SPINE):
    last_phase = pi == len(SPINE) - 1
    phase_marks.append((y - 11, phase))
    if body == "gateway":
        step += 1
        gl = [wrap(s_, 10.5, SPINE_W - 60) for _, s_ in GATEWAY]
        ih = 48 + sum(15 + len(L) * 13 + 8 for L in gl) + 2
        o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="12" fill="#13304f" stroke="#1b3c68"/>'
                 % (SPINE_X, y, SPINE_W, ih))
        o.append('<rect x="%d" y="%d" width="26" height="18" rx="5" fill="#e8622c"/>' % (SPINE_X + 12, y + 13))
        o.append('<text x="%d" y="%d" class="num">%d</text>' % (SPINE_X + 25, y + 26, step))
        o.append('<text x="%d" y="%d" class="bt" fill="#ffffff" font-size="13.5">The GenAI Gateway</text>' % (SPINE_X + 46, y + 27))
        yy = y + 48
        for (n, _), lines in zip(GATEWAY, gl):
            o.append('<circle cx="%d" cy="%.1f" r="2.5" fill="#e8622c"/>' % (SPINE_X + 20, yy - 4))
            o.append('<text x="%d" y="%d" class="gn">%s</text>' % (SPINE_X + 32, yy, esc(n)))
            for j, ln in enumerate(lines):
                o.append('<text x="%d" y="%d" class="gs">%s</text>' % (SPINE_X + 32, yy + 13 + j * 13, esc(ln)))
            yy += 15 + len(lines) * 13 + 8
        ch = callout(24, 282, y, "Why Cedar can read those claims", IDENTITY)
        y += max(ih, ch)
        arrow(CX, y + 7, y + 25); y += GAP
        continue
    alt = phase.startswith("Execution")
    if alt:
        step += 1
    for bi, (name, sub) in enumerate(body):
        if not alt:
            step += 1
        gate = phase.startswith("Short-circuit")
        if name == "EventBridge":
            callout(24, 282, y, "On failure", DLQ)
        h = box(SPINE_X, SPINE_W, y, name, sub,
                num=("%d%s" % (step, "ab"[bi])) if alt else str(step),
                tone="gate" if gate else "plain", tsize=13, ssize=11)
        if gate:
            gate_ys.append(y + h / 2)
        if name == "API Gateway response mapping":
            respmap_y = y + h / 2
        y += h
        if bi < len(body) - 1:
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

# ---- bypass rail ---------------------------------------------------------
rx, rw = 786, 250
r0, r1 = gate_ys[0] - 22, respmap_y
o.insert(0, '<rect x="%d" y="%.1f" width="%d" height="%.1f" rx="12" fill="#eef7f1" stroke="#c7e2d1"/>' % (rx, r0, rw, r1 - r0))
bl = wrap(BYPASS, 11, rw - 28)
for i, ln in enumerate(bl):
    o.append('<text x="%d" y="%.1f" class="byp">%s</text>' % (rx + 14, r0 + 26 + i * 15, esc(ln)))
for gy in gate_ys:
    o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#5e9e78" stroke-width="1.6" marker-end="url(#ahg)"/>'
             % (SPINE_X + SPINE_W + 4, gy, rx - 4, gy))
    o.append('<text x="%d" y="%.1f" class="elg">hit</text>' % (SPINE_X + SPINE_W + 14, gy - 6))
o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#5e9e78" stroke-width="1.4" stroke-dasharray="4 4"/>'
         % (rx + rw // 2, r0 + 26 + 15 * len(bl), rx + rw // 2, r1 - 10))
o.append('<text x="%d" y="%.1f" class="elg" text-anchor="middle">skips every step in between</text>' % (rx + rw // 2, r1 - 22))
o.append('<path d="M %d %.1f L %d %.1f L %d %.1f" fill="none" stroke="#5e9e78" stroke-width="1.6" marker-end="url(#ahg)"/>'
         % (rx + rw // 2, r1 - 10, rx + rw // 2, r1, SPINE_X + SPINE_W + 6, r1))

# ---- cross-cutting -------------------------------------------------------
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
 '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0,1 L9,5 L0,9 z" fill="#8fa0b6"/></marker>'
 '<marker id="ahg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0,1 L9,5 L0,9 z" fill="#5e9e78"/></marker></defs>',
 '<style>'
 '.dtitle{font-size:14.5px;font-weight:800;letter-spacing:.03em;fill:#0f2540;}'
 '.band{font-size:11px;font-weight:700;letter-spacing:.07em;fill:#8b96a5;text-transform:uppercase;}'
 '.num{font-size:10.5px;font-weight:700;fill:#fff;text-anchor:middle;}'
 '.bt{font-weight:700;}.bs{font-size:10.5px;}'
 '.lname{font-size:11.5px;font-weight:700;fill:#ffffff;letter-spacing:.02em;}'
 '.lmode{font-size:10px;font-weight:700;fill:#ffd8c4;letter-spacing:.05em;}'
 '.gn{font-size:11.5px;font-weight:700;fill:#ffffff;}.gs{font-size:10.5px;fill:#c9d5e3;}'
 '.ptitle{font-size:11px;font-weight:700;letter-spacing:.06em;fill:#16345c;text-transform:uppercase;}'
 '.phase{font-size:10.5px;font-weight:700;letter-spacing:.07em;fill:#8b96a5;text-transform:uppercase;}'
 '.rulehead{font-size:11.5px;font-weight:800;fill:#c94f1f;}.rule{font-size:11px;fill:#3a4a5e;}'
 '.conv{font-size:10px;font-weight:700;fill:#8b96a5;letter-spacing:.05em;}'
 '.orlab{font-size:10.5px;font-weight:700;fill:#8b96a5;letter-spacing:.08em;}'
 '.elg{font-size:10px;font-weight:700;fill:#3f8a60;}.byp{font-size:11px;font-weight:700;fill:#2f6b4c;}'
 '.cohead{font-size:10.5px;font-weight:800;fill:#16345c;}.co{font-size:10.5px;fill:#3a4a5e;}'
 '.cn{font-size:11px;font-weight:700;fill:#0b1524;}'
 '</style>',
 '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H),
 '<text x="24" y="32" class="dtitle">%s</text>' % esc(TITLE),
 '<line x1="24" y1="44" x2="%d" y2="44" stroke="#e3e7ee"/>' % (W - 24)]
for my, ph in phase_marks:
    head.append('<text x="%d" y="%d" class="phase">%s</text>' % (SPINE_X, my, esc(ph)))

SVG.write_text("\n".join(head + o) + "\n</svg>\n", encoding="utf-8")
print("wrote %s (%dx%d, %d converged steps)" % (SVG, W, H, step))
