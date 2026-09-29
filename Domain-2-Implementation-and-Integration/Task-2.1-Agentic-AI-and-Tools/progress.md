# Task 2.1 — Agentic AI Solutions and Tool Integrations — Progress Log

## Status

**Current step:** **Task complete.** All five parts of `project.md` built and live-tested,
Build Log page published, 6 bugs found and fixed. See *Standing cost and teardown* at the end.

**Path decision (Step 4):** Bedrock Agents classic is closed to this account, so the agent is a
code-first loop (Converse API + tool use) in Lambda, with memory in DynamoDB. Chosen because
notes §1.5 names DynamoDB explicitly for all three tiers and §6 requires a GSI design that a
managed memory service would hide. See Step 4.

**Scenario (from `project.md`):** an intelligent customer support system for an internet service
provider — multi-agent handling, session memory, safeguards, model coordination, human review,
external tool integration.

> Note: the scenario in `project.md` (ISP customer support) is **different** from the one in
> `notes.md` (global manufacturer / supply chain). Same Task 2.1 concepts, different domain.
> `notes.md` is the study material; `project.md` is the hands-on build.

**Decisions taken before build:**
- Default reasoning model: **Claude Haiku 4.5**. Claude Sonnet 4.5 is used only in the Part 4
  router, to demonstrate escalating to a stronger model. (~3x cheaper than Sonnet-everywhere;
  every routing lesson stays intact.)
- Scope: **all 5 parts** of the brief.
- Region: **us-east-1** (matches Domain 1).

## Resources Deployed

| Type | Name | Identifier | Step |
|---|---|---|---|
| IAM role | `adi-2-1-agent-role` | `arn:aws:iam::269737522732:role/adi-2-1-agent-role` | 2 |
| IAM role | `adi-2-1-lambda-role` | `arn:aws:iam::269737522732:role/adi-2-1-lambda-role` | 2 |
| S3 bucket | `adi-2-1-agent-schemas-269737522732` | us-east-1, public access blocked | 3 |
| Lambda | `adi-2-1-support-tools` | `arn:aws:lambda:us-east-1:269737522732:function:adi-2-1-support-tools` | 3 |
| DynamoDB | `adi-2-1-session-memory` | PK `sessionId` / SK `turnTimestamp`, TTL `expiresAt` | 5 |
| DynamoDB | `adi-2-1-decision-scratchpad` | PK `caseId` / SK `stepId`, TTL `expiresAt` | 5 |
| DynamoDB | `adi-2-1-strategic-memory` | PK `patternKey` / SK `observedAt`, GSI `issueCategory-observedAt-index` | 5 |
| Lambda | `adi-2-1-support-agent` | `arn:aws:lambda:us-east-1:269737522732:function:adi-2-1-support-agent` | 6 |
| IAM role | `adi-2-1-sfn-role` | `arn:aws:iam::269737522732:role/adi-2-1-sfn-role` | 7 |
| Lambda ×5 | `adi-2-1-parse-request`, `-determine-action`, `-action-handler`, `-reasoning`, `-generate-response` | one zip, five handlers | 7 |
| Step Functions | `adi-2-1-react-workflow` | `arn:aws:states:us-east-1:269737522732:stateMachine:adi-2-1-react-workflow` (STANDARD) | 7 |
| DynamoDB | `adi-2-1-circuit-breaker` | PK `serviceName` | 8 |
| Lambda | `adi-2-1-guarded-invoke` | `arn:aws:lambda:us-east-1:269737522732:function:adi-2-1-guarded-invoke` | 8 |
| CloudWatch alarm | `adi-2-1-circuit-open-alarm` | namespace `adi-2-1/Safeguards`, metric `CircuitOpened` | 8 |
| Lambda | `adi-2-1-model-router` | `arn:aws:lambda:us-east-1:269737522732:function:adi-2-1-model-router` | 9 |
| DynamoDB | `adi-2-1-human-reviews` | PK `reviewId`; GSIs `decisionType-createdAt-index`, `reviewerId-createdAt-index` | 10 |
| Lambda ×5 | `adi-2-1-evaluate-confidence`, `-create-review-task`, `-process-feedback`, `-deliver-response`, `-handle-review-timeout` | one zip, five handlers | 10 |
| Step Functions | `adi-2-1-hitl-workflow` | `arn:aws:states:us-east-1:269737522732:stateMachine:adi-2-1-hitl-workflow` (STANDARD) | 10 |

## Step Log

### Phase 0 — Foundations

#### Step 1 — Verify Bedrock model access and resolve the brief's retired model IDs

**What:** invoked each candidate model with a minimal prompt to confirm access before building
anything on top of it. All three returned successfully.

| Role in the build | Model ID used | Verified |
|---|---|---|
| Default reasoning / agent FM | `global.anthropic.claude-haiku-4-5-20251001-v1:0` | OK (14 in / 4 out) |
| Escalation target (Part 4 router) | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | OK (14 in / 4 out) |
| Cheap classifier (Part 4) | `amazon.nova-micro-v1:0` | OK (7 in / 2 out) |

**Where to check it:** AWS Console → Amazon Bedrock → *Model access* (us-east-1); and
Bedrock → *Inference and Assessment* → *Cross-region inference* for the profile IDs.

**Why:** every model named in `project.md` is retired and would fail at runtime. Confirming
access first turns a late `ValidationException` into a five-second check.

**Deviations from `project.md` (deliberate, not bugs):**

1. `anthropic.claude-3-sonnet-20240229-v1:0` — no longer on-demand invocable; survives only as a
   legacy inference profile. Replaced per the table above.
2. `amazon.titan-text-express-v1` — **retired entirely**. Only Titan *embedding* models remain in
   the account. Replaced with `amazon.nova-micro-v1:0`, its successor, which keeps the brief's
   cross-vendor "cheap model classifies, strong model reasons" lesson intact.
3. **No Claude model on Bedrock supports a bare `ON_DEMAND` model ID any more** — they all require
   an inference profile (`us.` or `global.` prefix). `aws bedrock list-foundation-models` confirms
   no Claude entry lists `ON_DEMAND` in `inferenceTypesSupported`. Pasting the brief's raw
   `modelId` strings returns a `ValidationException`.
4. The brief's agent definition uses
   `"memoryConfiguration": {"enableMemory": true, "memoryType": "SESSION_MEMORY"}`.
   The current API shape is `memoryConfiguration: {enabledMemoryTypes: ["SESSION_SUMMARY"],
   storageDays: N}` — `enabledMemoryTypes` is a required list with exactly one element, and
   `SESSION_SUMMARY` is the only permitted value.

**Also noted:** `project.md` is truncated — it cuts off in Part 5 Step 2 at `import boto3 /
import json`, so the human-review Lambda source is missing (it will be written from the
surrounding pattern). A stray line, `Successfully transferred back to supervisor`, is appended to
the end of the file as a copy-paste artifact.

**Cost of this step:** ~$0.00006 (three minimal invocations).

#### Step 2 — IAM roles for the agent and the Lambdas

**What:** two roles, each with a single tightly-scoped inline policy.

`adi-2-1-agent-role` — the Bedrock Agent service role.
- Trust: `bedrock.amazonaws.com`, further narrowed by `aws:SourceAccount` = 269737522732 and
  `aws:SourceArn` matching `arn:aws:bedrock:us-east-1:269737522732:agent/*`. This is the
  **confused-deputy guard**: without it, any Bedrock agent in any account could in principle
  induce Bedrock to assume this role.
- Permissions (`adi-2-1-agent-bedrock-invoke`): `bedrock:InvokeModel` /
  `InvokeModelWithResponseStream` on exactly the Haiku 4.5 global inference profile plus its two
  underlying foundation-model ARNs. Nothing else — the agent cannot reach Sonnet.

`adi-2-1-lambda-role` — shared execution role for every Task 2.1 Lambda.
- Trust: `lambda.amazonaws.com`.
- Permissions (`adi-2-1-lambda-task-policy`), four statements:
  - Logs scoped to `/aws/lambda/adi-2-1-*` — not account-wide `logs:*`.
  - Bedrock invoke on the three task models only (Haiku 4.5, Sonnet 4.5, Nova Micro), listing both
    the inference-profile ARN and every underlying foundation-model ARN.
  - DynamoDB `GetItem`/`PutItem`/`UpdateItem`/`DeleteItem`/`Query` on `table/adi-2-1-*` and its
    indexes. Note what is **absent**: no `dynamodb:*`, and no `DeleteTable`/`Scan`.
  - `states:SendTaskSuccess`/`SendTaskFailure`/`SendTaskHeartbeat` for the Phase 5 HITL callback.

**Where to check it:** AWS Console → IAM → *Roles* → `adi-2-1-agent-role` / `adi-2-1-lambda-role`
→ *Permissions* tab (inline policy) and *Trust relationships* tab.

**Why:** this is notes §4 layer 1 made concrete — *"action groups do not serve as security
boundaries; IAM policies do."* An agent that has been prompt-injected into calling
`delete_inventory` still cannot delete anything if the execution role was never granted the
permission. The boundary is enforced below the model, where no prompt can reach it.

**An honest limit worth recording:** the `states:SendTaskSuccess` statement uses `Resource: "*"`.
That is not laziness — **`SendTaskSuccess` does not support resource-level permissions**; you
cannot scope it to one state machine ARN. The authorization is carried by the task token itself,
which is a single-use secret issued per paused execution. So least privilege has a real ceiling:
some APIs are capability-based rather than resource-based, and the control moves from IAM to
protecting the token. Knowing *which* layer holds the boundary for a given API is the exam skill.

**Inference-profile IAM gotcha:** granting only the inference-profile ARN is **not enough**. The
profile fans out to regional foundation-model endpoints, and the call is authorized against those
too — so the underlying `foundation-model/*` ARNs must be listed alongside it. The `us.` Sonnet
profile routes to us-east-1, us-east-2 *and* us-west-2, so all three appear in the policy. Omit
them and you get an `AccessDeniedException` that names a region you never configured.

**Cost of this step:** $0 (IAM roles and policies are free).

### Phase 1 — Bedrock Agent with session memory

#### Step 3 — Action group backend: tool Lambda + OpenAPI schema

**What:** the three tools the support agent can call, plus the schema that tells it when to call
each one.

| Operation | Route | Returns |
|---|---|---|
| `getAccountStatus` | `GET /account-status` | plan, advertised speed, area code, billing status, balance |
| `getOutageStatus` | `GET /outage-status` | whether an area-wide outage is active, cause, restore ETA |
| `runLineDiagnostics` | `POST /line-diagnostics` | sync speed, packet loss, modem uptime, signal, verdict |

- `adi-2-1-support-tools` — Python 3.12, 256 MB, 15 s timeout, `adi-2-1-lambda-role`.
  Resource policy grants `lambda:InvokeFunction` to `bedrock.amazonaws.com`, conditioned on
  `AWS:SourceAccount` and `AWS:SourceArn` = `arn:aws:bedrock:us-east-1:269737522732:agent/*`.
  Log group retention set to **7 days** (cost control).
- `s3://adi-2-1-agent-schemas-269737522732/support-tools-openapi.json` — the OpenAPI 3.0 schema.
  All public access blocked.
- `data/isp-sample-data.json` — the generated sample dataset: 3 accounts across 3 service areas,
  2 active outages, and line readings per account. ACC-1001 is deliberately the interesting case
  (degraded line **and** an active outage in its area); ACC-1002 is deliberately `past_due` with a
  healthy line, so billing status is the real answer rather than the hardware.

**Where to check it:** Console → Lambda → Functions → `adi-2-1-support-tools` → *Configuration* →
*Permissions* (resource-based policy); and S3 → `adi-2-1-agent-schemas-269737522732`.

**Why:** the action group is the agent's hands. This step builds the hands before the brain so the
agent has something real to call the moment it is created.

**Verified:** eight cases locally (happy path per tool, lowercase normalisation, unknown account,
missing parameter, unknown operation), then a live `lambda invoke` of the deployed function —
`POST /line-diagnostics` for ACC-1001 returned `200` with `pct_of_plan_speed: 2.4`
(12 Mbps against a 500 Mbps plan), `verdict: degraded`.

**Two notes-driven design choices, deliberately visible in the code:**

1. **§7 — model-readable errors.** The consumer of these error strings is the *model*, not a human
   reading a log. An unknown account returns
   `{"error": "No account matches 'BOGUS'...", "error_class": "fixable", "valid_account_ids": [...]}`
   — the valid alternatives travel with the error so the agent can self-correct on the next turn
   instead of apologising to the customer. Errors are classified `fixable` / `retryable` / `fatal`,
   and the `fatal` message explicitly instructs the agent to stop rather than retry.
2. **§4 layer 2 — input validation.** Every parameter arrives from the model, so none is trusted.
   `_require_account` normalises and allow-lists against known ids before any lookup. The OpenAPI
   schema constrains *types*; only the Lambda can enforce *business rules*.

**A schema detail that does real work:** the OpenAPI `description` fields are the agent's
instruction manual — §7 calls the schema the agent's prompt, and it is literal. `getOutageStatus`
says *"Call this FIRST whenever a customer reports slow connectivity"* and explains that its
`area_code` must come from `getAccountStatus` rather than from the customer. That ordering is not
enforced in code anywhere; it is taught purely through prose the model reads. Thin descriptions are
the most common cause of an agent picking the wrong tool.

**Cost of this step:** ~$0 (2 Lambda invocations, 5.6 KB in S3; all inside free tier).

#### Step 4 — BLOCKED: Bedrock Agents (classic) is in Maintenance Mode

**What happened:** `aws bedrock-agent create-agent` was rejected outright:

```
AccessDeniedException: Bedrock Agents is in Maintenance Mode. New agent creation is not
available for accounts without prior service usage.
```

This account has never created a Bedrock Agent (`list-agents` returns empty), so it falls on the
wrong side of that grandfather clause. **No IAM change or quota request fixes this** — the classic
`bedrock-agent` control plane is closed to new accounts. `adi-2-1-agent-role` was created in Step 2
for an agent that cannot now exist; it is harmless and costs nothing, and is reused by whichever
replacement path is chosen.

**Why this matters beyond this task:** Part 1 of `project.md` is built entirely on the classic
Bedrock Agents API, and so is a large amount of Task 2.1 reference material. The managed
"create an agent, attach an action group, prepare, alias" flow is the *previous* generation.
**Amazon Bedrock AgentCore** is the successor, and it is available in this account
(`bedrock-agentcore-control` responds; runtimes and memories both list empty). Worth knowing cold:
an exam answer naming classic Bedrock Agents for a greenfield build is now describing a service
new accounts cannot provision.

**What was verified instead — the agent loop itself works.** Before choosing a replacement, the
Reason → Act → Observe loop was proven end to end against the Step 3 tools using the
**`bedrock-runtime` Converse API with tool use**, which is the same loop a managed agent runs
internally. One run, with the model given only the tool schemas and the ordering instruction:

```
ACT  getAccountStatus({'account_id': 'ACC-1001'})  -> area_code AREA-NORTH, Fibre 500 Mbps, current
ACT  getOutageStatus({'area_code': 'AREA-NORTH'})  -> active: true, INC-4471, fibre cut
FINAL: "There's an active outage in your area caused by a fibre cut during municipal roadworks
        affecting 1,840 customers. The estimated restoration time is 10:00 PM tonight."
stopReason: end_turn | usage: 1,069 in / 63 out
```

The model called the tools **in the right order**, passed `area_code` from the first result into
the second, and correctly did **not** suggest rebooting the modem during a known outage. That is
notes §1's core loop working with nothing managed about it — which is precisely why the classic
agent is replaceable here.

**Cost of this step:** ~$0.0015 (one Haiku 4.5 loop, 1,069 in / 63 out).

**Replacement options costed** (us-east-1, live from the Pricing API):

| Path | What changes | Cost |
|---|---|---|
| Hand-rolled loop + DynamoDB memory | Loop in Lambda via Converse API; memory tiers in DynamoDB | ~$0 idle; $0.625/M writes |
| Hand-rolled loop + **AgentCore Memory** | Same loop; memory becomes the managed service | $0.00025/event short-term; $0.00075/memory-month long-term; $0.0005/retrieval |
| Full **AgentCore** (Runtime + Memory + Gateway) | Agent packaged as an ARM64 container in ECR; tools exposed as MCP via Gateway | Runtime $0.0895/vCPU-hr + $0.00945/GB-hr while a session runs; Gateway $5/M invocations + $0.0002/tool-index-month |

#### Step 5 — Three-tier memory hierarchy in DynamoDB

**What:** the three memory tiers from notes §1.5, one table each, all `PAY_PER_REQUEST`.

| Tier | Table | Key schema | Lifecycle |
|---|---|---|---|
| Operational (session) | `adi-2-1-session-memory` | PK `sessionId`, SK `turnTimestamp` (N) | TTL on `expiresAt` |
| Tactical (scratchpad) | `adi-2-1-decision-scratchpad` | PK `caseId`, SK `stepId` | TTL on `expiresAt` |
| Strategic (long-term) | `adi-2-1-strategic-memory` | PK `patternKey`, SK `observedAt` (N) | **no TTL** — persistent |

`adi-2-1-strategic-memory` carries a GSI, `issueCategory-observedAt-index`
(PK `issueCategory`, SK `observedAt`, projection ALL).

**Where to check it:** Console → DynamoDB → *Tables* → each table. TTL is under
*Additional settings*; the GSI is under *Indexes* on `adi-2-1-strategic-memory`.

**Why each choice was made — this is the examinable part:**

- **Sort keys encode the access pattern.** Session memory is always read as *"the last N turns of
  this conversation, in order"*, so `turnTimestamp` as a numeric sort key makes that a single
  `Query` with `ScanIndexForward=false` and a `Limit`. No filtering, no scan.
- **TTL is per tier, not global.** Operational and tactical memory expire because a stale
  scratchpad is worse than no scratchpad — it feeds the agent facts that were true an hour ago.
  Strategic memory has **no TTL**, because the whole point of the tier is that it outlives the
  incident. Notes §1.5 gives 90 days as a typical session TTL; the value is written per item at
  write time rather than baked into the table, so different session types can age differently.
- **The GSI exists to avoid a Scan.** Base-table access is *"what happened to this specific
  pattern"*. But the question the business actually asks is *"show me every billing-related issue
  from the last week"* — a different partition key entirely. Without the GSI that is a full table
  scan, which gets more expensive every day the table grows. This is the same design notes §6
  prescribes for the human-review feedback table in Phase 5, rehearsed one tier early.
- **On-demand billing, deliberately.** Provisioned capacity would bill around the clock for a PoC
  that is idle 99% of the time. On-demand is $0 when nothing is happening.

**Verified:** all three tables `ACTIVE`; TTL reports `Enabled` on `expiresAt` for the two
short-lived tiers; the GSI is live on the strategic table.

**Cost of this step:** $0 — empty tables on on-demand billing cost nothing, and storage sits far
inside the 25 GB free tier. Writes are $0.625/M, reads $0.125/M.

#### Step 6 — The agent loop, over the memory tiers

**What:** `adi-2-1-support-agent` — Python 3.12, 512 MB, 120 s timeout, 7-day log retention.
The Reason → Act → Observe loop a managed agent would run internally, written out explicitly:

- **Reason** — `bedrock:Converse` with `toolConfig`, Haiku 4.5, `maxTokens` 700, `temperature` 0.2.
- **Act** — any `toolUse` blocks are dispatched to `adi-2-1-support-tools`.
- **Observe** — results are returned as `toolResult` blocks and the loop repeats until
  `stopReason` is `end_turn` or `MAX_ITERATIONS` (6) is hit.
- **Operational memory** — prior turns are reloaded at the start of every invocation and each new
  turn is written back with a 90-day `expiresAt`, so context survives across separate invocations.
- **Tactical memory** — every tool call is written to the scratchpad *as it happens* (§2.2: a
  failure on iteration 4 does not destroy the evidence from iterations 1-3).

**Where to check it:** Console → Lambda → `adi-2-1-support-agent`; DynamoDB → `adi-2-1-session-memory`
(query a `sessionId` to see the turns) and → `adi-2-1-decision-scratchpad` (the tool trace).

**Why:** this is Part 1 of the brief — *"maintains conversation context across interactions"* —
working without the managed agent that is no longer available.

**Also required:** `adi-2-1-lambda-role` was missing `lambda:InvokeFunction`. Added as a fifth
statement, scoped to `function:adi-2-1-*` rather than `*`.

---

**Bug 1 — the agent confabulated the customer's plan on turn 2.**

*Symptom.* A two-turn session. Turn 1: *"my internet has been crawling, account ACC-1001"* — the
agent called both tools and correctly reported the outage. Turn 2: *"remind me what plan I am on?"*
— the agent answered **"You're on the 100 Mbps plan."** The real plan is **Fibre 500 Mbps**. It did
not call a tool and it did not hesitate.

*Root cause.* Operational memory stores the **conversation** — what the agent said out loud. Turn
1's answer was about the outage and never mentioned the plan, so on turn 2 the reloaded context
contained no plan fact at all. The tactical scratchpad *did* have it
(`getAccountStatus -> {"plan": "Fibre 500 Mbps", ...}`), but nothing ever read that tier back. Faced
with a question it had no fact for, the model produced a plausible-looking number rather than
admitting the gap — and the system prompt's *"never invent"* instruction did not save it, because a
prompt cannot restore information that is not in the context window.

*Fix.* Added `load_established_facts(case_id)` — a `Query` against the scratchpad partition — and
injected the results into the system prompt as an authoritative facts block, with an instruction to
quote them exactly and to call a tool or admit ignorance for anything not listed. Re-tested on a
fresh session: turn 2 now answers **"You're on the Fibre 500 Mbps plan"** with **zero tool calls**,
recalled from tactical memory.

*Why it matters beyond this bug.* The tiers in §1.5 are not just three places to put data — they
carry **different kinds** of data. Operational memory is the dialogue; tactical memory is the
evidence. An agent that reloads only the dialogue has amnesia for everything it learned but did not
say, and that amnesia surfaces as confident fabrication rather than as an error. Prompt instructions
cannot fix a context-window problem.

---

**Verified — three scenarios:**

| Scenario | Tool calls | Outcome |
|---|---|---|
| ACC-1001 turn 1, slow connection | 2 (`getAccountStatus` → `getOutageStatus`) | Reported the fibre cut and 10 PM restore; correctly did **not** suggest rebooting |
| ACC-1001 turn 2, "what plan am I on?" | 0 | `priorTurnsLoaded: 2`; answered "Fibre 500 Mbps" from tactical memory |
| ACC-1002, "nothing I do fixes it" | 1 (`getAccountStatus`) | Stopped at `past_due` / $89.50 and did **not** run diagnostics on a healthy line |

That third case is the one worth noticing: the agent spent **one** tool call, not three. The
schema description told it that a past-due balance explains a dead connection on its own, so it
never reached for the diagnostic. Tool-ordering prose doing real work.

**Cost of this step:** ~$0.03 (five loop runs, ~14k input / 800 output on Haiku 4.5).

### Phase 2 — ReAct with Step Functions

#### Step 7 — The ReAct state machine

**What:** nine states and five Lambdas. The same Reason → Act → Observe cycle as Phase 1, but the
macro structure now lives in a state machine instead of a `for` loop.

| State | Lambda | Role |
|---|---|---|
| `ParseUserRequest` | `adi-2-1-parse-request` | **No LLM** — regex intent + account-id extraction |
| `DetermineAction` | `adi-2-1-determine-action` | LLM picks one of troubleshoot / billing / escalate / none |
| `ActionChoice` | — | `Choice` routing to the three branches |
| `TroubleshootingAction` / `BillingAction` / `EscalateAction` | `adi-2-1-action-handler` | Executes the chosen action |
| `ReasonAboutResults` | `adi-2-1-reasoning` | LLM judges whether the facts explain the issue |
| `MaxIterationsGuard` | — | `Choice` — loop back only if the model wants more **and** `iteration < 3` |
| `GenerateResponse` | `adi-2-1-generate-response` | Final customer-facing reply |

`TimeoutSeconds: 300` on the machine; `Retry` with exponential backoff on every Task; `Catch` on the
two LLM states routing to `GenerateResponse` so a planner failure degrades to an answer rather than
a dead execution.

**Where to check it:** Console → Step Functions → *State machines* → `adi-2-1-react-workflow` →
*Executions*. The visual graph shows the three branches and the loop-back edge.

**Why:** notes §2.1 — the hybrid approach. The developer owns the macro-level structure (a fixed,
auditable sequence of states) while the model owns micro-level reasoning inside each state.

**Deviation from `project.md`:** the brief defines three separate Lambdas
(`TroubleshootingFunction`, `BillingFunction`, `EscalateFunction`). Here all three `Choice` branches
invoke one `adi-2-1-action-handler` with a different `action` in the payload. The state machine
graph still shows three distinct paths — the teaching point — while the code, IAM and deployment
stay in one place. Three near-identical functions would have been three cold starts to warm and
three copies to keep in sync.

---

**Bug 2 — the brief's own state machine can loop forever.** Its `NeedMoreActions` state is:

```json
"NeedMoreActions": {
  "Type": "Choice",
  "Choices": [{"Variable": "$.needMoreActions", "BooleanEquals": true, "Next": "DetermineAction"}],
  "Default": "GenerateResponse"
}
```

There is **no iteration bound**. The only thing standing between that workflow and an unbounded
Bedrock spend is the model's willingness to eventually answer `false` — which is precisely the
judgement notes §4 says must never be trusted. This build replaces it with `MaxIterationsGuard`,
which `And`s the model's vote together with `iteration < 3`. The model still gets to vote; it just
cannot outvote the ceiling.

**Verified — three branches:**

| Input | Actions taken | Iterations | Confidence | Outcome |
|---|---|---|---|---|
| "crawling all morning, ACC-1001" | `troubleshoot` | 1 | 0.95 | Named the fibre cut, 1,840 affected, 10 PM restore |
| "overcharged on my last bill, ACC-1002" | `billing`, `billing` | 2 | 0.75 | Surfaced the $89.50 past-due balance, offered escalation |
| "third outage this month, I want to cancel, ACC-1003" | `escalate` | 1 | 0.95 | Opened ticket ESC-1790640442 |

**The loop-back edge, proven from the execution history** of the billing run:

```
ParseUserRequest -> DetermineAction -> ActionChoice -> BillingAction -> ReasonAboutResults
  -> MaxIterationsGuard -> DetermineAction        (loop 1)
  -> ActionChoice -> BillingAction -> ReasonAboutResults
  -> MaxIterationsGuard -> DetermineAction        (loop 2)
  -> ActionChoice -> GenerateResponse             (planner returned "none")
```

**An observation from that run, not a bug.** The billing branch executed **twice with identical
inputs** and gathered nothing new the second time. The planner has no memory of what it has already
done — each `DetermineAction` call sees the accumulated results but reasons afresh, and on the
second pass it judged the same evidence insufficient again. Left unbounded, that is exactly how a
ReAct loop burns budget without making progress: not by going haywire, but by politely repeating
itself. The ceiling is what turns a wasteful loop into a bounded one, and the confidence score
dropping to 0.75 (against 0.95 for the clean single-pass runs) is the signal that would route this
case to a human in Phase 5.

**Cost of this step:** ~$0.02 (three workflow runs, ~30 state transitions, ~12 LLM calls on Haiku).

### Phase 3 — Safeguarded AI workflows

#### Step 8 — Timeout budget, circuit breaker, alarm

**What:** `adi-2-1-guarded-invoke` wraps every Bedrock call in two independent protections, backed
by `adi-2-1-circuit-breaker` (PK `serviceName`) and surfaced by `adi-2-1-circuit-open-alarm`.

**Layer 3 — timeout.** The budget is derived from
`context.get_remaining_time_in_millis()` minus a 3 s reserve, and applied as a botocore
`read_timeout` with `retries={"max_attempts": 0}`. The model can therefore never be the thing that
runs the function out of time; on expiry the failure is recorded and a fallback returned.

**Layer 5 — circuit breaker.** `CLOSED → OPEN → HALF_OPEN → CLOSED`, with failures counted in a
rolling 300 s window. Opens at >50% failures over at least 5 calls; 60 s cooldown; a single
HALF_OPEN probe either closes it or re-opens it immediately.

**Where to check it:** Console → Lambda → `adi-2-1-guarded-invoke`; DynamoDB →
`adi-2-1-circuit-breaker` (watch `status` change live); CloudWatch → *Alarms* →
`adi-2-1-circuit-open-alarm`, and *Metrics* → `adi-2-1/Safeguards`.

**Verified — the full state cycle, driven with injected failures:**

```
healthy call            servedBy=model     circuit=CLOSED   ok=1 fail=0
inject failure  1       servedBy=fallback  circuit=CLOSED   rate=0.50
inject failure  2       servedBy=fallback  circuit=CLOSED   rate=0.67
inject failure  3       servedBy=fallback  circuit=CLOSED   rate=0.75
inject failure  4       servedBy=fallback  circuit=OPEN     rate=0.80  <- opened
inject failure  5       servedBy=fallback  circuit=OPEN     (refused without attempting)
... 60 s cooldown ...
next call               servedBy=model     circuit=CLOSED             <- HALF_OPEN probe passed
```

The fifth call is the one that matters: `ok=None fail=None` because the breaker returned **before
touching the model or the counters**. That is the difference between a breaker and a retry policy —
under sustained failure the load on the failing dependency drops to zero instead of continuing.

---

**Bug 3 — the brief's circuit-breaker code does not run.** `project.md` Part 3 Step 2:

```python
UpdateExpression="SET calls = if_not_exists(calls, :empty_list) + :call"
```

Tested verbatim against DynamoDB:

```
ValidationException: Invalid UpdateExpression: Incorrect operand type for
operator or function; operator or function: +, operand type: L
```

`+` in an update expression is arithmetic only. List concatenation needs `list_append()`, which was
confirmed working on the same table. Two further problems with that design even once fixed: the
`calls` list grows without bound toward the 400 KB item limit and is re-read and filtered in the
client on every single call; and `error_rate > 0.5` with no minimum sample size means **the first
failed call is a 100% error rate** and trips the breaker for everyone. This build uses `ADD`
counters with a rolling window (O(1) forever) and a `MIN_CALLS` floor of 5.

---

**Bug 4 — the brief's IAM policy grants nothing.** `project.md` Part 3 Step 2 also offers a policy
capping token count and temperature:

```json
{"Effect":"Allow","Action":["bedrock:InvokeModel"],"Resource":"*",
 "Condition":{"NumericLessThan":{"bedrock:MaxTokens":"2000"},
              "NumericLessThanEquals":{"bedrock:Temperature":"0.5"}}}
```

Run through `iam simulate-custom-policy`:

| Simulation | Decision | Missing context |
|---|---|---|
| No context supplied | `implicitDeny` | `bedrock:Temperature`, `bedrock:MaxTokens` |
| **Both keys supplied and satisfied** (500 < 2000, 0.2 ≤ 0.5) | **`implicitDeny`** | *(none)* |

It denies **even when the conditions are met**, because `bedrock:MaxTokens` and
`bedrock:Temperature` are not real IAM condition keys. IAM authorises an API call from its action,
its resource ARN and a fixed set of service-published condition keys — it **cannot inspect request
body parameters** such as `temperature` or `max_tokens`. As written, that statement is worse than
useless: it grants nothing while looking like a guardrail. Inference parameters must be capped in
application code, which is what `inferenceConfig={"maxTokens": 300, "temperature": 0.2}` does here.

---

**Bug 5 — the alarm was watching a metric that does not exist.** The alarm sat at `OK` through two
separate breaker trips. The first explanation reached for was CloudWatch ingestion latency — the
period was widened from 60 s to 300 s on that theory. **That diagnosis was wrong.** The real cause:

```
alarm's configured dimensions            -> []
metric queried with no dimensions        -> 0 datapoints
metric queried with ServiceName=cb-demo  -> 3 datapoints
```

`put-metric-alarm` was called with `--namespace` and `--metric-name` but **no `--dimensions`**,
while the Lambda publishes with `ServiceName`. A CloudWatch metric is identified by namespace **+**
name **+** its complete dimension set, so an alarm with no dimensions watches a genuinely different
metric — one that has never had a datapoint. It reported `OK` truthfully and forever.

Recreated with `--dimensions Name=ServiceName,Value=bedrock-haiku` and re-verified against a live
trip. The widened 300 s period was kept: it is still the right setting for a one-off event metric,
just not the fix for this.

**Cost of this step:** ~$0.01 (2 real model calls; the 16 failure injections never reached Bedrock).

### Phase 4 — Model coordination

#### Step 9 — The routing layer

**What:** `adi-2-1-model-router`. Nova Micro classifies the request (`taskType` × `complexity`), a
routing table picks the model, runtime signals can downgrade that choice, and a fallback chain
covers failure. Every decision is priced from the live AWS Pricing API rates.

| Model | Bedrock id | In $/MTok | Out $/MTok | Routed for |
|---|---|---|---|---|
| Nova Micro | `amazon.nova-micro-v1:0` | 0.035 | 0.14 | classification, routing, short extraction |
| Haiku 4.5 | `global.anthropic.claude-haiku-4-5-...` | 1.10 | 5.50 | standard support reasoning, tool use |
| Sonnet 4.5 | `us.anthropic.claude-sonnet-4-5-...` | 3.30 | 16.50 | multi-constraint reasoning, escalations |

**Where to check it:** Console → Lambda → `adi-2-1-model-router` → *Test*, or CloudWatch Logs for
the routing decision on each call.

**Verified — six cases, measured not asserted:**

| # | Input | Classified | Routed to | Total cost | Sonnet equivalent |
|---|---|---|---|---|---|
| A | "What time does your support line open?" | classification / low | **nova-micro** | $0.0000141 | $0.0007689 |
| B | Credit promised twice, speed short, disputed late fee, legal threat | reasoning / **high** | **sonnet** | $0.0019365 | $0.0019272 |
| C | Same as B, `requireFast: true` | reasoning / high | **haiku** (downgraded) | $0.0005908 | $0.0017457 |
| D | Same as B, `maxCostUsd: 0.0002` | reasoning / high | **nova-micro** (downgraded twice) | $0.0000197 | $0.0011946 |
| E | Same as B, sonnet throttled | reasoning / high | **haiku** (fallback) | $0.0007118 | $0.0021087 |
| F | Same as B, sonnet **and** haiku throttled | reasoning / high | **nova-micro** (fallback ×2) | $0.0000183 | $0.0010296 |

Case A is the whole argument for routing in one line: **$0.0000141 against $0.0007689** — the same
answer, 54× cheaper, because "what time do you open" never needed a frontier model. Case B shows
the router declining to save money when the request genuinely warrants Sonnet.

**Latency tells the same story.** Case A answered in **470 ms**; case B took **3,819 ms**. Notes §5
claims dynamic selection cuts response time 42% — the mechanism is visible here: it is not that any
model got faster, it is that most requests stop being sent to the slow one.

**Case D's downgrade chain**, walking the fallback ladder until the estimate fits the budget:

```
budget $0.0002: sonnet -> haiku      (est $0.007413)
budget $0.0002: haiku  -> nova-micro (est $0.002471)
```

**Case F's attempt record**, the fallback chain under sustained throttling:

```json
[{"model":"sonnet","ok":false,"error":"ThrottlingException"},
 {"model":"haiku","ok":false,"error":"ThrottlingException"},
 {"model":"nova-micro","ok":true}]
```

The customer still got an answer. §5's point about fallbacks is exactly this: a cheaper answer
beats an error page.

**Deviation from `project.md`:** the brief routes on `taskType` alone. This build routes on
`taskType` **×** `complexity`, because task type alone cannot separate "summarise this note" from
"summarise this five-way dispute" — and the second genuinely needs the better model. The brief also
names `amazon.titan-text-express-v1` as the classifier, which is retired (Step 1); Nova Micro is its
successor and is 30× cheaper than Haiku on input.

**Not built: ensembles.** §5's fourth strategy runs N models and combines by majority vote or
weighted average, treating disagreement as an escalation signal. It is deliberately skipped here:
at N calls per request it is the most expensive strategy in the section, and for this PoC it would
demonstrate nothing the routing table does not already show. Worth knowing for the exam as the
high-cost / high-confidence option, and as the one whose *disagreement* is the useful output.

**Cost of this step:** ~$0.005 (six router runs, 12 model calls).

### Phase 5 — Human in the loop

#### Step 10 — Task-token review gate

**What:** seven states and five Lambdas implementing the §6 escalation bands, backed by
`adi-2-1-human-reviews` with two GSIs.

| Confidence | Sensitivity | Route | Behaviour |
|---|---|---|---|
| > 0.9 | NORMAL | `AUTO` | Sent immediately, no review record |
| 0.7 – 0.9 | NORMAL | `ASYNC_REVIEW` | Sent immediately **and** a review row written for later |
| < 0.7 | NORMAL | `SYNC_REVIEW` | Execution **parks** until a human responds |
| any | HIGH | `SYNC_REVIEW` | Always parks — confidence cannot override sensitivity |

**Where to check it:** Console → Step Functions → `adi-2-1-hitl-workflow` (a parked execution sits
in `RequestHumanReview` and shows as RUNNING at zero cost); DynamoDB → `adi-2-1-human-reviews`.

**Deviation from `project.md` — the poll loop is replaced by a task token.** The brief's Part 5 uses
`Wait → CheckHumanReviewStatus → Choice → Wait`. That bills a state transition per poll, adds
latency averaging half the poll interval, and still needs the reviewer's answer stored somewhere the
poller can read. `.waitForTaskToken` with `$$.Task.Token` inverts it: the execution parks at **zero
cost and zero transitions** until someone calls `SendTaskSuccess`. `TimeoutSeconds: 86400` gives
§6's 24-hour fallback, caught by `States.Timeout` into `HandleReviewTimeout`, which escalates to a
human queue rather than silently sending an unreviewed reply.

**Verified — the pause/resume cycle:**

```
start execution            -> RUNNING, parked in RequestHumanReview
DynamoDB row               -> rev-786bee6fb4aa, cancellation, conf 0.45, HIGH, PENDING,
                              taskToken stored (660 chars)
... execution stays RUNNING, no polling, no transitions ...
send-task-success          -> verdict REJECTED, reviewer agent-priya-k, correction supplied
execution                  -> SUCCEEDED, the human's text replaced the model's draft
```

**Verified — all three bands plus the override:**

| Case | Confidence | Sensitivity | Route |
|---|---|---|---|
| Outage question **with facts supplied** | 0.92 | NORMAL | `AUTO` |
| "Why is my service slow", facts show past_due + healthy line | 0.72 | NORMAL | `ASYNC_REVIEW` |
| Intermittent evening drops, diagnostics healthy | 0.62 | NORMAL | `SYNC_REVIEW` |
| "Refund for the downtime" | 0.65 | **HIGH** (`terms ['refund']`) | `SYNC_REVIEW` |
| "Cancel my service and refund" | 0.45 | **HIGH** | `SYNC_REVIEW` |

---

**Bug 6 — every customer with an "issue" was escalated to a human.** Sensitivity was matched with
`any(term in text for term in SENSITIVE_TERMS)`, and `"sue"` is a substring of `"issue"`:

```
'I have an issue with my internet'  -> ['sue']   flagged HIGH
'My connection has issues'          -> ['sue']   flagged HIGH
'pursue a complaint'                -> ['sue']   flagged HIGH
```

"Issue" is one of the most common words in support traffic, so this routed a large share of
ordinary tickets to synchronous human approval — quietly destroying the automation the whole system
exists to provide, while looking like a conservative safety setting. Replaced with a word-boundary
regex, with `\w*` on the stems that are meant to be prefixes so `cancellation` and `compensation`
still match. A second pass added a negative lookahead for `credit card` / `credit score`, which were
matching as credit *requests*. Verified clean on all of the above while still catching `cancel`,
`cancellation`, `compensation`, `refund`, `sue`, and account `credit`.

---

**A design flaw found by testing, not by reading.** The first `AUTO` test parked instead of
auto-approving: *"Is there an outage in my area?"* scored **0.35**. Nothing was broken — the HITL
workflow has **no tools**, so the model was correctly unsure about a fact it had no way to look up.
But it means a confidence gate placed in front of a tool-less model sends nearly everything to a
human. The gate has to run **after** fact-gathering, not instead of it. Added a `facts` channel that
carries the ReAct workflow's findings into the evaluation prompt. The same question, unchanged:

```
without facts -> confidence 0.35 -> SYNC_REVIEW (parked)
with facts    -> confidence 0.92 -> AUTO        (sent immediately)
```

Worth holding onto: a model's self-assessed confidence is largely a statement about **how much
context it was given**, not about how capable it is. Low confidence across the board is a signal to
look at the pipeline feeding the model, not at the model or the threshold.

---

**Verified — the GSIs, and what they are actually for (§6):**

```
GSI decisionType-createdAt-index, "every cancellation review":
  Query  scanned 1 item, returned 1
GSI reviewerId-createdAt-index, "what has agent-priya-k handled":
  Query  scanned 1 item, returned 1
    model drafted : "Thank you for contacting us. I'd be happy to help you cancel..."
    human sent    : "I can help with cancelling. Before we proceed, I should mention
                     there is an active outage in your area..."
Same question with no GSI:
  Scan   scanned 6 items, returned 1     <- reads the entire table
```

`ScannedCount` is the number that matters: the Query touches only matching items, the Scan touches
everything and throws most of it away. At six rows that is invisible; at six million it is the
difference between a dashboard and an outage. The second query is also where the value of the
feedback loop shows — storing the draft **and** the human's correction side by side is what makes
"where does the model keep getting it wrong" answerable.

**Cost of this step:** ~$0.02 (roughly a dozen evaluate-confidence calls on Haiku 4.5).

## Concepts Explained

- **Route on task shape, not model ranking.** "Which model is best" is the wrong question; "what
  does this request actually need" is the right one. A classifier costing four millionths of a
  dollar decides where a call 50× more expensive goes.
- **Complexity is a separate axis from task type.** Two requests of the same type can need
  different models. Collapsing them into one dimension either overpays on the simple case or
  underperforms on the hard one.
- **Dynamic selection means runtime signals can override the table.** Remaining budget and latency
  requirements are known only at call time. The table is the default, not the decision.
- **A fallback chain converts an outage into a degradation.** Falling from Sonnet to Haiku to Nova
  Micro still answers the customer. Design the chain by what each model can still do adequately,
  not merely by price.

- **Inference profiles vs. model IDs.** Bedrock now fronts most current models with cross-region
  inference profiles. The `us.` prefix routes within US regions; `global.` routes worldwide for
  better availability. A bare `anthropic.*` model ID is only directly invocable if the model lists
  `ON_DEMAND` in `inferenceTypesSupported` — which no current Claude model does. Exam-relevant:
  "why does my `InvokeModel` call fail with `ValidationException` on a model I can see in the
  console" is an inference-profile question.
- **Model retirement is a real lifecycle concern** (ties back to Task 1.2). Reference architectures
  written against a model ID go stale; routing through a profile and keeping the ID in config
  rather than in code is what makes the swap a one-line change.
- **Confused-deputy protection on service roles.** A trust policy naming only a service principal
  (`bedrock.amazonaws.com`) is global to that service. `aws:SourceAccount` + `aws:SourceArn`
  conditions bind it to *your* resources, so another account's agent can't borrow it.
- **Least privilege has a ceiling.** Some APIs (`states:SendTaskSuccess` among them) don't support
  resource-level permissions. When IAM can't hold the boundary, something else must — here, the
  single-use task token. Recognising which control actually enforces a given operation matters
  more than reflexively writing narrow ARNs.
- **The OpenAPI schema is a prompt, not just a contract.** Type constraints stop malformed calls;
  the `description` text is what makes the agent choose the *right* tool in the right order. Time
  spent on descriptions buys more reliability than time spent on schema strictness.
- **Design errors for the model.** A bare `404` ends the agent's turn. A 404 carrying the valid
  alternatives plus an `error_class` lets it recover without human involvement. Retryable vs.
  fixable vs. fatal is the distinction that decides whether the loop continues, corrects, or stops.
- **Bedrock Agents (classic) is in Maintenance Mode.** New accounts cannot create one; AgentCore is
  the successor. Reference architectures and study material written around
  `create-agent` / action groups / `prepare-agent` / aliases describe a closed door for greenfield
  work. Recognising which generation a given exam answer belongs to is now part of the question.
- **A managed agent is a loop you could write yourself.** The Converse API with `toolConfig` gives
  the same Reason → Act → Observe cycle: the model returns `toolUse` blocks, you execute them and
  hand back `toolResult` blocks, and you repeat until `stopReason` is `end_turn`. What the managed
  service adds is memory, tracing, versioning and alias management — not the reasoning itself. This
  is exactly the Bedrock Agents vs. Strands distinction in notes §1.4.
- **Memory tiers are distinguished by lifetime and access pattern, not by technology.** All three
  tiers here are DynamoDB; what differs is the key schema, whether TTL is on, and which index
  answers the real question. Choosing ElastiCache for the operational tier would be about latency
  (sub-millisecond reads inside a tool-call loop), not about it being "a different kind of memory".
- **A GSI is how you avoid paying for a Scan.** When the business question uses a different
  partition key than the write path does, that is the signal for a secondary index. Recognising
  that moment — rather than reaching for `Scan` with a filter — is the DynamoDB judgement the exam
  tests, and notes §6 asks for it by name.
- **Operational memory is the dialogue; tactical memory is the evidence.** Reloading only the
  conversation gives an agent amnesia for every fact a tool returned that it did not happen to
  mention — and the failure mode is confident fabrication, not an error. Feeding the tactical tier
  back into context is what makes multi-turn agents factually stable.
- **A prompt cannot fix a missing-context problem.** "Never invent a fact" was already in the
  system prompt when Bug 1 happened. Instructions govern behaviour over the context the model has;
  they cannot conjure information that was never loaded. When an agent hallucinates a specific
  value, check what is actually in its context before rewriting the prompt.
- **Stopping conditions belong in the harness.** `MAX_ITERATIONS` is enforced by the `for` loop, so
  no instruction, tool result, or model decision can extend it. Notes §4 layer 4 in one construct.
- **Workflow CoT is recoverable; prompt CoT is not.** Each handler writes its output to the
  scratchpad before returning, so a failure at `ReasonAboutResults` leaves the parse and action
  results durable and inspectable. The same reasoning inside one LLM call would vanish entirely.
- **`Retry` and `Catch` are the graceful-degradation half of §4.** Retries absorb transient Lambda
  throttling; `Catch` on the two LLM states routes a hard failure to `GenerateResponse` so the
  customer gets an answer rather than a hung execution. Failing *to an answer* beats failing loudly.
- **Deterministic parsing before model reasoning (§2.3).** `ParseUserRequest` uses regex, not an
  LLM: it runs in microseconds, costs nothing, always applies the same rules, and hands downstream
  steps a structured contract. Reach for the model only where judgement is actually required.
- **A circuit breaker is not a retry policy.** Retries increase load on a failing dependency;
  a breaker removes it. Once OPEN, calls are refused locally without touching the dependency at
  all — which is what gives the downstream service room to recover.
- **A minimum sample size is part of the threshold.** "Error rate > 50%" is meaningless on one call.
  Without a floor, the first transient failure takes the feature down for every user.
- **Catching your own errors hides you from CloudWatch.** `adi-2-1-guarded-invoke` returns 200 with
  a fallback, which is correct behaviour — and means the built-in `AWS/Lambda` `Errors` metric stays
  flat while the system is fully degraded. Graceful degradation has to emit its own signal, hence
  the custom `CircuitOpened` metric. A dashboard that looks healthy during an outage is the failure
  mode to design against.
- **IAM cannot police request payloads.** It authorises on action, resource ARN and published
  condition keys. Limits on inference parameters, prompt content or output length live in
  application code — no policy can enforce them.
- **A task token is the right shape for a human pause.** Polling bills transitions and adds latency
  to something that may take hours. `.waitForTaskToken` parks the execution for free and resumes it
  the instant a human answers. The trade is that the token *is* the capability — store it
  deliberately, and make sure the timeout path cleans it up.
- **Sensitivity must override confidence, never the reverse.** Confidence says how sure the model
  is; sensitivity says how much a mistake costs. A confident wrong refund is worse than a hesitant
  right one, so a HIGH-sensitivity action gates at any confidence.
- **Keyword matching needs word boundaries.** `"sue" in "issue"` is the whole of Bug 4. Substring
  checks on short words fail silently and in the *safe* direction, which is exactly why nobody
  notices: the system looks cautious rather than broken.
- **Low confidence is usually a context problem.** Before tuning a threshold or blaming the model,
  check what the model was actually given. 0.35 → 0.92 on the identical question came from supplying
  facts, not from changing the model, the prompt bands, or the threshold.

## Standing cost and teardown

**Total build cost: ~$0.09**, against a $1.50–2 estimate. Bedrock tokens dominated, as predicted;
the saving came from Haiku 4.5 being the default and from most failure-path testing (16 injected
failures) never reaching a model at all.

**Standing cost when idle: effectively $0.** Nothing in this build bills by the hour:

| Resource class | Idle cost | Why |
|---|---|---|
| Lambda ×14 | $0 | Pay per invocation |
| Step Functions ×2 | $0 | Pay per state transition; a *parked* task-token execution transitions nothing |
| DynamoDB ×5 | $0 | On-demand billing, storage far inside the 25 GB free tier |
| S3 (1 object, 5.6 KB) | ~$0 | Negligible |
| CloudWatch alarm ×1 | $0.10/month | Within the 10-alarm free tier |
| CloudWatch Logs ×14 groups | <$0.10/month | 7-day retention set on every group at creation |

Worst case ≈ **$0.10–0.20/month**, and that assumes the alarm falls outside the free tier. There is
no Route 53 health check, no provisioned throughput, no NAT gateway, no container, and no
always-on endpoint — the recurring-cost shapes worth checking for after any build.

**Two things that would drift if left unattended:**

1. **Parked HITL executions.** A `.waitForTaskToken` execution holds for its full
   `TimeoutSeconds` (86,400 = 24 h). They cost nothing, but they sit in the console as RUNNING.
   Four test executions were stopped explicitly rather than left to expire.
2. **`adi-2-1-agent-role`** is orphaned — created in Step 2 for the Bedrock Agent that Maintenance
   Mode prevented. Harmless and free; kept as evidence of the blocker.

**To tear the whole task down:**

```bash
export AWS_PROFILE=awsgenai AWS_REGION=us-east-1
# Lambdas
for f in support-tools support-agent parse-request determine-action action-handler \
         reasoning generate-response guarded-invoke model-router evaluate-confidence \
         create-review-task process-feedback deliver-response handle-review-timeout; do
  aws lambda delete-function --function-name adi-2-1-$f
  aws logs delete-log-group --log-group-name /aws/lambda/adi-2-1-$f 2>/dev/null
done
# State machines (stop any parked executions first)
for sm in react-workflow hitl-workflow; do
  ARN=arn:aws:states:us-east-1:269737522732:stateMachine:adi-2-1-$sm
  for e in $(aws stepfunctions list-executions --state-machine-arn $ARN \
             --status-filter RUNNING --query 'executions[].executionArn' --output text); do
    aws stepfunctions stop-execution --execution-arn $e --cause teardown
  done
  aws stepfunctions delete-state-machine --state-machine-arn $ARN
done
# Tables, bucket, alarm
for t in session-memory decision-scratchpad strategic-memory circuit-breaker human-reviews; do
  aws dynamodb delete-table --table-name adi-2-1-$t
done
aws s3 rb s3://adi-2-1-agent-schemas-269737522732 --force
aws cloudwatch delete-alarms --alarm-names adi-2-1-circuit-open-alarm
# Roles (inline policies must go first)
for r in agent-role lambda-role sfn-role; do
  for p in $(aws iam list-role-policies --role-name adi-2-1-$r --query 'PolicyNames[]' --output text); do
    aws iam delete-role-policy --role-name adi-2-1-$r --policy-name $p
  done
  aws iam delete-role --role-name adi-2-1-$r
done
```

**Recommendation: leave it running.** At roughly $0.10/month this is cheap to keep as a working
reference, and the ReAct and HITL state machines are the two artefacts most worth re-reading before
the exam — the visual graph of a bounded ReAct loop and a task-token pause explains both concepts
faster than any note does.
