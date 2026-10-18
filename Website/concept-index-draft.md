# Concept Index — draft for review

Source: all 20 `notes.md` files (2,961 lines). Each entry has:

- **Owner** — the one task whose notes carry the real detail. Read this page first.
- **Also appears in** — every other task that touches it, *and the different reason it shows up there*.

Review question for each entry: **is the owner right?** That's the call that matters — the owner
is what the site will send you to when a concept confuses you.

Legend: 55 concepts, 7 groups. Counts in brackets = how many of the 20 tasks touch it.

---

## Group A — Data & retrieval: the RAG spine

### A1. Chunking [15 tasks, all 5 domains]
**Owner: 1.5** — four strategies (fixed-size, structure-aware, hierarchical parent–child, semantic),
Bedrock KB's five options including Lambda custom chunking, ~10% boundary overlap, and the exam rule:
chunking strategy is chosen *per document type*, not uniformly across a corpus.
**Also appears in:**
- **4.1** — chunking for *cost*, not retrieval quality. Too large wastes input tokens on noise; too small
  needs more chunks and adds prompt overhead. (The notes flag this 1.5-vs-4.1 split explicitly.)
- **5.2** — chunking as the *bug*. Fixed-size chunking decoupled research findings from their methodology;
  the fix was structure-aware chunking preserving `[Methodology] + [Findings] + [Conclusions]`.
- **2.5** — a different thing with the same name: *request* chunking + recursive summarization to fit a
  prompt inside a token window, not to index a corpus.
- **1.3** — chunking as one stage of the five-stage pre-inference pipeline.
- **4.3** — chunk hygiene *before* indexing (Glue, Data Wrangler), because bad data is near-impossible to
  remove once embedded.

### A2. Embeddings & dimensionality [11, all 5]
**Owner: 1.5** — Titan at 1,536 dims (V2 also 1024/512/256), dense vs sparse, binary embeddings + FP16
quantization for ~32× storage reduction, domain-vocabulary mismatch ("consideration", "party"), and the
golden rule: the same embedding model must serve both ingestion and query, or the vector space shifts and
the corpus needs a full rebuild.
**Also appears in:**
- **5.2** — *embedding drift* and domain misalignment, diagnosed by projecting vectors with SageMaker and
  looking at the clustering. Its verdict is the sharp one: domain fit matters more than dimensionality.
- **3.2** — scrub PII *before* embedding. Once PII is in vector coordinates it's mathematically opaque and
  can't be cleanly deleted.
- **3.1** — embeddings reused for *verification* rather than retrieval: embed the answer, compare it to the
  source chunks, and low similarity means fabrication.
- **2.2** — the embedding *cache*, so repeated phrasings don't re-invoke the embedding model.
- **4.1** — the economics: generating an embedding is negligible next to an LLM call, which is what makes
  semantic caching pay.

### A3. Vector store selection [12, all 5]
**Owner: 1.4** — Bedrock KB (managed/public), OpenSearch + neural plugin (confidential + hybrid),
RDS + S3 + custom store (metadata pre-filter → vector math → raw file), DynamoDB for live flags; plus
sharding, parallel fan-out, and fine-grained access control evaluated *before* vector math runs.
**Also appears in:**
- **1.1** — the decision matrix and its hard exam rule: OpenSearch Serverless is mandatory for SaaS
  connectors (SharePoint, Salesforce, Confluence). Also S3 Vectors for scale, Aurora pgvector for existing
  Postgres, Neptune Analytics for GraphRAG multi-hop.
- **1.5** — multi-tenant shapes: silo / pool / bridge, and the warning that pool-model tenant filters must
  live in the query layer, never in client code.
- **4.3** — *operating* one: index fragmentation, query-latency drift, and snapshot restore (minutes) vs
  re-embedding the corpus (hours/days + full inference cost).
- **4.2 / 5.2** — index algorithm choice, below.

### A4. ANN index algorithms [2 tasks, but two different treatments]
**Owner: 5.2** — the four-way comparison: LSH (fast, low recall), HNSW (best speed/accuracy, memory-hungry),
IVF (scalable, moderate memory), PQ (lossy compression, tiny footprint) — and the conclusion that there is
no best one; benchmark against your own dataset.
**Also appears in:**
- **4.2** — how to *tune* the one you picked: HNSW's `m` and `ef_construction` affect build time and RAM;
  `ef_search` affects query latency and recall. `ef_construction` has zero effect on query speed — a classic
  exam trap.

### A5. Hybrid search (dense + BM25) [4]
**Owner: 1.5** — why both are needed (dense for concepts, sparse for statute codes and proper nouns),
configured via `OverrideSearchType = HYBRID`, and the constraint that the store must support hybrid scoring.
**Also appears in:**
- **1.4** — the worked example: "Section 10b-5" needs keyword, "fraudulent stock practices" needs semantic.
- **4.2** — hybrid feeding a *custom reranker*: `Final Score = Relevance·w₁ + Recency·w₂ + Authority·w₃`.
- **5.2** — hybrid as the prescribed *fix* when retrieval returns irrelevant results (ICD-10 codes).

### A6. Reranking & two-stage retrieval [3]
**Owner: 1.5** — stage 1 retrieves top 100 cheaply, stage 2 reranks to top 10 with cross-attention, because
running cross-attention over 15M documents is computationally impossible.
**Also appears in:**
- **4.2** — reranking as weighted domain logic (recency and authority, not just relevance).
- **2.5** — dynamic RAG: scale `k` by query complexity (k=3 simple, k=20 complex), then cross-encoder rerank.

### A7. Query expansion & decomposition [3]
**Owner: 1.5** — expansion adds alternative terminology for up to +23% recall; decomposition splits
multi-part questions into parallel sub-queries via Step Functions for up to −40% latency.
**Also appears in:**
- **4.2** — a fuller preprocessing pipeline upstream of the vector DB: normalization, stop-word removal,
  spelling correction (typos produce bad vector projections), then expansion.
- **5.2** — model-driven query rewriting with domain synonyms and acronyms as a retrieval fix.

### A8. Metadata & filtering [4]
**Owner: 1.4** — taxonomies and structured attributes, AI-powered tagging at ingestion, and the
cross-reference graph that blocks a 100%-semantic-match case because it was overturned on appeal.
**Also appears in:**
- **1.5** — timing: metadata must be attached *during* chunking. Adding it later means full re-ingestion.
- **3.3** — the same tags as *governance*: `DataSensitivity`, `RegulatoryScope`, `Jurisdiction`, driving
  tag-based access control, with SCPs denying creation of untagged resources outright.
- **2.5** — Q Business doing metadata extraction for you, as a managed service.

---

## Group B — Model choice, routing, money

### B1. Model cascading [5]
**Owner: 4.1** — the tiered-routing vs cascading table, model choice as the single largest cost lever
(up to 80% vs 10–20% from prompt work and caching), and the rule: set the quality bar first, then buy the
cheapest model that clears it.
**Also appears in:**
- **2.2** — framed as *cost*: a small model answers ~80% of queries; the trade-off is that escalated
  queries cost two calls and *more* latency, so cascading only pays if most queries really are simple.
- **2.4** — framed as *routing*: confidence 0.7–0.9 triggers escalation, and intermediate findings are
  passed forward so the big model doesn't restart from nothing.
- **2.1** — as a fallback mechanism inside dynamic model selection (−42% response time).
- **2.3** — centralized: the GenAI Gateway owns cascading and failover for every team at once.

### B2. Confidence thresholds [15, domains 1–4]
**Owner: 2.1** — the escalation ladder: >0.9 fully automated, 0.7–0.9 automated with async human review,
<0.7 synchronous approval before anything executes, with Step Functions wait tokens holding state.
**Also appears in — the number repeats, what it gates does not:**
- **2.4** — 0.7–0.9 decides whether to escalate to a *bigger model*.
- **2.5** — 80–90% for critical decisions; UI must visually separate AI-generated from human-verified.
- **1.6** — <0.70 Comprehend intent confidence triggers a *clarification question*, not an escalation.
- **3.1** — high / medium / low decides answer / answer-plus-disclaimer / block-and-review.
- **3.3** — confidence is *weighted down* when the underlying data source is less reliable.
- **3.4** — where the number comes from: token log-probs, ensemble disagreement, and calibration (a "90%"
  answer should be right 90% of the time).
- **1.2** — internal confidence drops tracked as a production failure mode.

### B3. Provisioned Throughput vs On-Demand [4]
**Owner: 4.1** — break-even analysis. Buy provisioned only when on-demand token spend exceeds the Model Unit
commitment; below that you are buying idle capacity. Under-utilized PMUs waste money, over-utilized PMUs
cause 429s.
**Also appears in:**
- **2.2** — the sizing formula (peak RPS × avg tokens/request → required TPS → Model Units) and the term
  commitment you're billed for even if traffic drops.
- **4.2** — the same purchase for a *throughput* reason, plus cross-region inference profiles.
- **3.2** — IAM restricting *which* feature a role may use — provisioned vs on-demand as a permission.

### B4. Batch inference vs request batching [3]
**Owner: 4.1** — the disambiguation the exam leans on. Bedrock Batch is a *cost* feature (~50% discount,
offline). Request batching is a *throughput* feature (GPU utilization at runtime). Same word, unrelated.
**Also appears in:**
- **4.2** — batch + SQS micro-batching for throughput, and the honest trade-off: batching serves more people
  and makes each wait longer.
- **2.2** — continuous batching to stop GPU starvation; Batch Transform as an endpoint type.

### B5. Caching — five different caches [10, domains 1/2/4]
**Owner: 4.1** — semantic caching at 85–95% similarity (70% returns wrong answers, 99% behaves like
exact-match), result fingerprinting via deterministic hashing, prompt caching at ~90% discount on the static
prefix *only if the static part comes first*, and the L1/L2/L3 tiering. Hit rate below 5% means the cache
costs more than it saves.
**Also appears in:**
- **2.2** — embedding cache vs response cache as two separate layers with different keys and values.
- **2.3** — caches stacked across API Gateway, ElastiCache and the database, plus invalidation mechanics
  (TTL, event-driven purge, write-through).
- **2.5** — the client-side one, matching at 85–95% similarity rather than exact text.
- **4.2** — pre-computation as a cache: ~3,000 ms model call becomes a ~10 ms key-value lookup.
- **1.4** — a query cache for hot statutes and boilerplate.

### B6. Token economics [20 — every single task]
**Owner: 4.1** — billed twice and unevenly (output costs more per token than input), pre-call counting for
cost prediction and context-limit validation, context pruning (drop 30% of noise → 30% cheaper), `max_tokens`
as the cheapest single change, "lost in the middle" so critical instructions go first, and "summarize once,
reuse many times" — because a summary is itself a model call.
**Also appears in:**
- **2.5** — token windowing and recursive summarization; prompt-chaining reduction by compression,
  summarization, or key-information extraction (the last being most reliable, as summaries drift).
- **4.2** — the same reductions for *speed*: shorter prompts execute faster and free concurrency.
- **4.3** — a 10× token spike as a *bug report*: context leakage or an agent in a loop.
- **5.2** — context overflow causing **silent truncation**. No error is thrown; the model drops trailing
  context and answers confidently anyway. The 8,000-token wall.
- **3.4** — token count per demographic as a proxy metric for *completeness bias*.

---

## Group C — Prompting & output control

### C1. Chain-of-Thought [4]
**Owner: 1.6** — why it works: models generate tokens sequentially, so forcing the reasoning out first puts
each step into working memory for the next. Plus the auditability benefit — the chain is logged even when
hidden from the user.
**Also appears in:**
- **2.1** — *workflow*-based CoT instead of prompt-based. Each reasoning step is a separate call persisting
  to state, so step 4 failing doesn't destroy steps 1–3. Worth +37% decision quality.
- **3.4** — the exact opposite UI decision from 1.6: *show* the reasoning, because transparency outranks
  simplicity in a clinical setting.
- **5.2** — CoT as a *diagnostic instrument* — make the model show its work to find where the logic broke.

### C2. Prompt versioning & rollback [5, all 5 domains]
**Owner: 1.6** — prompts are code artifacts. Bedrock Prompt Management versions them; rollback is a pointer
move from v8 to v7 in seconds with no redeploy. Three-tier approval (author → compliance → admin) with
separation of duties so nobody ships their own prompt.
**Also appears in:**
- **5.2** — automated rollback on a *threshold*: v6 91% → v7 94% → v8 88% → auto-revert to v7.
- **2.5** — the prompt registry as a *debugging* tool: latency spiked because v8, shipped yesterday,
  doubled the prompt length.
- **3.4** — the same discipline applied to guardrail JSON, rubrics and templates via IaC.
- **3.3** — joint artifact versioning for reproducibility (see F3).

### C3. Golden datasets & regression testing [4]
**Owner: 1.6** — the v7-vs-v8 table where International Transfers fell 91% → 73% and the pipeline blocked
the deploy, even though Joint Accounts improved 62% → 94%. Fixing one scenario commonly breaks another.
**Also appears in:**
- **5.1** — the same gate inside CodePipeline producing a hard `RELEASE BLOCKED` state, plus the rule that
  changing the eval dataset makes v7 and v8 scores statistically non-comparable.
- **3.1** — golden datasets pointed at *accuracy* regressions in banking answers.
- **4.3** — golden datasets are what turn "hallucination" into a number an alarm can watch.

### C4. Temperature, top-p, top-k [4]
**Owner: 4.2** — the full parameter table and the key mechanic: top-k is a *fixed count* regardless of model
certainty; top-p is *adaptive* — few candidates when confident, many when not.
**Also appears in:**
- **1.3** — why insurance locks 0.0–0.2 (the same claim must reach the same conclusion tomorrow), and the
  golden rule stated plainly: tune temperature *or* top-p, never both, because the effects overlap and you
  can no longer debug why behavior shifted.
- **3.4** — the same knobs as *in-processing policy controls*.
- **5.1** — A/B testing temperature and top_p as the worked example of comparative analysis.

### C5. JSON Schema & structured output [5]
**Owner: 1.6** — text instructions ask; schema *enforces*. Marking `disclaimer` as required makes legally
mandated text structurally impossible to drop, where a prompt only makes it probable.
**Also appears in:**
- **3.1** — schema catches a failure mode semantic similarity can't: a perfectly-formed response with a 150%
  interest rate. Conversely, semantic similarity catches perfectly-formed JSON full of invented rules.
  Different layers, different blind spots.
- **1.2** — JSON validity >95% as a hard gate, and the real-world break: the model appends ```json fencing
  and the downstream EHR parser dies.
- **2.4** — schema validation at *API Gateway*, before a token is spent, enforcing `max_tokens <= 4096`.
- **5.2** — schema enforcement across both templates and responses as prompt maintenance.

### C6. Flows vs Agents — deterministic vs autonomous [4]
**Owner: 1.6** — the comparative matrix: execution path, behavioral consistency, auditability, industry fit.
Regulated work wants a fixed graph a regulator can inspect; exploratory work wants ReAct.
**Also appears in:**
- **1.1** — the short version: Flows node-based and predictable, Agents ReAct and dynamic.
- **2.1** — the hybrid that dissolves the dichotomy: **Step Functions ReAct** — macro-deterministic state
  machine, micro-non-deterministic reasoning inside each state. Stopping conditions and auditability
  without giving up intelligence.
- **2.5** — Prompt Flows as a *non-developer* tool: drag-and-drop for business analysts.

---

## Group D — Agents

### D1. The agent loop & memory tiers [6]
**Owner: 2.1** — Reason → Act → Observe; the three Bedrock Agent components (FM, instructions, action groups)
plus optional KB and guardrails; single vs multi-agent; Bedrock Agents vs Strands vs Agent Squad; and the
three-tier memory hierarchy — operational (ElastiCache/DynamoDB), tactical (DynamoDB scratchpad), strategic
(S3/KB).
**Also appears in:**
- **2.5** — Agent Squad supervision and *handoff validation*: if Agent A read it as auto collision and
  Agent B as property damage, halt rather than pass bad context downstream.
- **3.4** — agent *tracing* (`enableTrace=true`) exposing reasoning paths, KB retrievals with relevance
  scores, tool payloads and per-step confidence — for debugging and for proving which sources were used.
- **4.3** — the AgentCore tab in CloudWatch, handoff idle time, and loop detection: a tool that normally
  runs 100×/day firing 5,000×/hour.

### D2. Agent runaway control — five non-interchangeable layers [4]
**Owner: 2.1** — IAM least privilege (action groups are *not* a security boundary), input validation on
model-generated parameters (block `delete_inventory(quantity: -500)`), timeouts, stopping conditions
(max iterations, max time, confidence), circuit breakers with graceful degradation.
**Also appears in:**
- **2.5** — rate limiting in the tool config as a sixth layer.
- **4.1** — stopping conditions as pure *cost* control against recursive loops.
- **4.3** — the bill as the *detector*: runaway agents and denial-of-wallet attacks show up on cost first.
- **2.3** — WAF rate-based rules against the same attack from outside.

### D3. Tool definitions — OpenAPI, action groups, MCP [4]
**Owner: 2.1** — the OpenAPI schema *is* the agent's instruction manual, so descriptions decide whether the
right tool gets picked; two-level parameter validation (Bedrock for types, Lambda for business rules);
model-readable errors (return valid alternatives, not `404`, so the agent self-corrects); action groups are
Bedrock-only while MCP is portable; Lambda for short stateless tools vs ECS for heavy stateful ones.
**Also appears in:**
- **1.5** — MCP as the "USB cable" standard between models and enterprise data, plus function calling that
  lets the model choose `search_cases()` or `check_overturned()`.
- **2.5** — the same OpenAPI spec written for *humans* — partner integrations — rather than for an LLM.
- **4.3** — the diagnostic inversion: a 40% tool failure rate is almost never the API's fault. It means the
  tool *description* is ambiguous and the model is passing bad parameters.

---

## Group E — Safety, security, privacy

### E1. Guardrails [13, all 5 domains]
**Owner: 3.1** — the two execution modes (block the whole response vs filter out just the bad part), content
filter severity with its counter-intuitive inversion — **LOW is the strictest setting, HIGH blocks only
extreme content** — denied topics, word filters, and a clear statement of what guardrails *cannot* do.
**Also appears in:**
- **1.6** — guardrails as layer 2 of instruct/block/structure, sitting *outside* the model and the prompt,
  which is exactly why prompt injection can't disable them; one policy applies across Claude, Llama and Nova.
- **3.4** — context-aware guardrails, multi-stage filtering at different sensitivities per stage, the
  two-layer model (built-in FM filters + an external LLM judge for nuanced rules), and the safety-vs-utility
  cost: aggressive filters block legitimate clinical words like "bleeding" and "dosage".
- **3.2** — guardrails for *privacy*: PII filters and role-contextual configuration, so one model serves a
  doctor and a billing clerk under different rules.
- **1.1** — an independent safety net outside the inference path.
- **3.3** — the output-filtering stage of the closed governance loop.
- **2.5** — content-filtering middleware as the hand-rolled equivalent.

### E2. Defense in depth & the cheap-to-expensive ordering [4]
**Owner: 3.1** — WAF → Lambda regex → Comprehend → Guardrails → model, ordered by cost, and the blind-spot
table that justifies every layer: WAF can't read "ignore previous rules"; Comprehend misses zero-days;
Guardrails can't check whether *this* account belongs to *this* user; post-processing is too late to stop the
token bill. Throttling is listed as a *security* control — it stops brute-forcing prompt variants.
**Also appears in:**
- **1.6** — the three-layer version: prompt instructs, guardrails block, schema structures.
- **3.4** — pre- / in- / post-processing policy enforcement.
- **2.3** — the enterprise request lifecycle: federation → Cognito trigger → WAF → PrivateLink → IAM →
  Verified Permissions → KMS → CloudTrail.

### E3. Prompt injection vs jailbreak; direct vs indirect [4]
**Owner: 3.1** — injection *overrides instructions*, jailbreak *bypasses filters* (role-play, hypotheticals,
Base64/ROT13, language switching, multi-turn probing). And the architectural danger: **indirect** injection
hides the payload in a document that RAG later retrieves, so it fires for an innocent user's query.
**Also appears in:**
- **1.6** — why system prompts alone are not a defense.
- **1.2** — red teaming as adversarial testing, with the negated-statement trap.
- **3.1** — red teaming as a four-stage Step Functions loop that breeds new attack variants from successes.
- **3.3** — misuse anomaly detection: off-hours access, 100× volume spikes, systematic probing.

### E4. PII / PHI handling [10, domains 1–4]
**Owner: 3.2** — the masking table that everything else references: redaction (irreversible, least context),
tokenization (reversible, consistent references), pseudonymization (reversible, most context, reads as natural
text), format-preserving encryption (keeps length and shape for strict parsers). Then dataset-level
anonymization — generalization, perturbation, synthetic data — plus differential privacy with its ε budget
(without a budget, repeated queries average the noise away) and k-anonymity. And the named failure mode:
over-anonymizing until the data is useless, which is why the pipeline needs a utility check.
**Also appears in:**
- **3.1** — why a post-processing Lambda is still needed next to guardrails: guardrails replace an entity
  with `[PII]`, but compliance wants `XXXX-XXXX-XXXX-1234` with a Luhn check, and deterministic code is the
  fail-safe for a guardrail false negative.
- **3.3** — token-level redaction via endpoint handlers, combining regex with NER.
- **1.5** — redact before embedding (see A2).
- **1.2** — de-identify before data touches a training pipeline, for BAA/HIPAA.
- **4.3** — turning on model invocation logs captures full prompts and responses, so PII becomes a logging
  problem too.
- **2.3** — tokenization so real values never cross a jurisdictional boundary.

### E5. Comprehend vs Macie — PII in two places [2]
**Owner: 3.2** — Comprehend works on *text in flight* at request time (25+ PII types; Comprehend Medical for
PHI and clinical entities). Macie works on *data at rest in S3*, discovering and classifying with built-in
and custom identifiers. Picking the wrong one is a stock exam distractor.
**Also appears in:** **3.1** (Comprehend as layer 2 of input safety, scoring risk for branching).

### E6. Network isolation [3]
**Owner: 3.2** — Bedrock is a public service by default. The interface-vs-gateway endpoint table is the
detail: interface endpoints create an ENI with a private IP and are governed by security groups and NACLs;
gateway endpoints exist only for S3 and DynamoDB, live in the route table, consume no subnet IPs, and have no
security groups. Plus private subnets with no IGW/NAT and strict egress filtering.
**Also appears in:**
- **2.2** — PrivateLink to SageMaker endpoints.
- **2.3** — endpoint *policies* that restrict calls to `claude-*` and to `bedrock:InvokeModel` only,
  forbidding fine-tuning or deletion; Transit Gateway black-hole routes guaranteeing no Dev→Prod path;
  Network Firewall domain filtering to stop exfiltration from a compromised component.

### E7. IAM & access models [several, domains 1–4]
**Owner: 3.2** — least privilege on three axes (specific models, specific features, specific operations),
RBAC vs ABAC (ABAC scales without a new policy per condition), condition keys including `aws:sourceVpce`,
resource-based policies on KBs and custom models, and Lake Formation for column / row / cell-level control
*inside* tables used for training and RAG.
**Also appears in:**
- **2.3** — condition keys for source IP and business hours, permission boundaries as a ceiling on delegated
  admin, Verified Permissions + Cedar for application-level authorization (IAM says *can you call Bedrock*,
  Cedar says *may you see this document in this context*), and RAM for cross-account sharing.
- **3.3** — the three-layer hierarchy: SCPs set a ceiling and never grant (root in a member account cannot
  escape one) → IAM grants → resource policies; plus tag-based access control.
- **2.1** — stated bluntly: action groups are not a security boundary, IAM policies are.
- **1.4** — FGAC evaluated against the JWT *before* vector math runs, so unauthorized matches never score.

### E8. Edge & data residency — move the model to the data [3]
**Owner: 2.3** — the three options and their distinct motives: **Outposts** for residency when law forbids
data leaving premises, **Local Zones** for metro-area latency, **Wavelength** inside 5G carrier networks for
mobile. Plus Direct Connect with BGP policies prioritizing inference over bulk sync on a shared link, and
Control Tower blocking non-compliant deployments before provisioning.
**Also appears in:**
- **3.2** — VPC isolation as the in-region version of the same instinct.
- **2.4** — Route 53 failover that must respect residency boundaries.

---

## Group F — Governance & responsible AI

### F1. CloudTrail vs CloudWatch Logs [5, domains 1–4]
**Owner: 1.6** — the table: CloudTrail records API *metadata* (who called InvokeModel, when, which prompt
version, which model) kept ~7 years for regulators. CloudWatch Logs records *payloads* (full prompt, full
response, tokens, latency) for operational debugging.
**Also appears in:**
- **3.3** — the distinction that decides exam questions: **management events are on by default, data events
  are OFF**. Without enabling data events you cannot prove which S3 objects were read during training or RAG
  context assembly. Plus multi-region trails and Athena for audit reports.
- **4.3** — the two paired for forensic reconstruction after an incident.
- **3.2** — the wider stack: CloudTrail + Logs Insights + GuardDuty + Security Hub with automated remediation.

### F2. Model Cards [2]
**Owner: 3.3** — SageMaker Model Cards as both birth certificate and report card: intended use and explicit
*un*supported uses, data lineage, evaluation metrics, risks and guardrails, SEC/FINRA fields, fairness and
explainability scores. And the operational point — generate them *programmatically in CI/CD*, because manual
documentation goes stale the moment a model retrains.
**Also appears in:**
- **3.4** — Bedrock Model Cards from the Responsible-AI angle, with *disaggregated* metrics per demographic
  group, so high aggregate accuracy can't hide a failing cohort.

### F3. Lineage & reproducibility [2]
**Owner: 3.3** — lineage as a DAG of Artifacts (S3 URIs, weights, metrics files, ECR images), Actions
(ETL, training jobs) and Contexts (endpoints, experiments, pipeline runs); Glue tracks *data* lineage while
SageMaker tracks *model* lineage; cross-account `AddAssociation` keeps the chain unbroken; S3 versioning plus
Feature Store time travel; and the guarantee regulators actually want — same model version + same data
version = same output.
**Also appears in:**
- **5.1** — the practical corollary: prompts, weights and eval datasets version together as one snapshot,
  or v7-vs-v8 scores mean nothing.

### F4. Bias & fairness metrics [2 tasks, two different maths]
**Owner: 3.4** — the fairness criteria: demographic parity (and its flaw — forcing equal rates distorts when
base rates genuinely differ), equal opportunity (TPR parity), equalized odds (strictest — TPR *and* FPR), and
counterfactual fairness, called out as the most practical for GenAI because changing only the demographic
attribute isolates causation. Group vs individual fairness. Plus **completeness bias**: factually correct but
systematically *shorter* answers for one cohort is still bias.
**Also appears in:**
- **3.3** — SageMaker Clarify's three computed metrics: DPPL (difference in positive proportions), DI
  (disparate impact — below 0.8 is the red flag), DCR (difference in conditional rejection); and the
  pre-training vs post-training bias split.
- **3.4 again** — policy translation turning that into a deployable control: DI tolerance 0.8–1.25, emitted
  to CloudWatch, with an alarm that halts the deploy.

### F5. Drift — five unrelated things [11, all 5 domains]
**Owner: 3.3** — SageMaker Model Monitor's four modules, which is the only place drift is taxonomized:
data quality drift, model quality drift (needs ground-truth labels), bias drift, and feature attribution
drift. Measured with Jensen-Shannon divergence against a training-time baseline, and needing careful
threshold calibration to balance false alarms against missed drift.
**Also appears in — same word, different thing:**
- **1.2** — *data* drift: new medications, ICD-10 revisions, changed physician shorthand.
- **5.2** — *embedding* drift: the vector space diverges as new literature introduces new terminology.
- **1.6** — *prompt* drift: 30 regional prompt files where updates fail to propagate evenly.
- **2.5** — *multi-agent* drift, which supervision exists to prevent.
- **4.2 / 4.3** — *latency* drift and index degradation accumulating invisibly day to day.
- **5.1** — regression benchmarking against a fixed dataset as the detector for behavioral drift.

### F6. Human in the loop [several, all 5 domains]
**Owner: 2.1** — the mechanism, not just the principle: confidence bands decide the review mode, Step
Functions **wait tokens** pause the workflow and preserve state (with a 24-hour timeout) rather than
terminating, and corrections land in DynamoDB with GSIs by decision type and reviewer so rejection patterns
can be queried without a table scan.
**Also appears in:**
- **1.6** — three-tier approval with separation of duties, and the feedback loop where a human agent's *edit*
  becomes ground truth driving prompt v9.
- **1.2** — the three-tier evaluation gate ending in non-negotiable clinical sign-off.
- **1.3** — failed validation is never silently discarded; it routes to a human review queue.
- **5.1** — the two audiences and why both are needed: customers judge helpfulness but cannot detect a
  confident hallucination; only domain experts catch factual and regulatory errors.
- **3.3** — separation of duties as governance: whoever trained the model cannot approve its deployment.

---

## Group G — Running it in production

### G1. Retry, backoff, jitter, circuit breaker [5, domains 2 & 5]
**Owner: 2.4** — the actual numbers: backoff 100/200/400/800 ms, jitter ±100 ms, 3–5 attempts, a 20 s cap
(without a cap exponential growth compounds into minutes), breaker trips at 50% failures over 10 requests,
30–60 s recovery, half-open at 10–20% traffic to test before fully reopening.
**Also appears in:**
- **2.5** — split by *status code*, which is the sharper framing: 429 retries almost immediately with
  100–300 ms jitter because capacity will return; 5xx backs off exponentially from 500 ms; 4xx never retries
  because it will fail identically forever.
- **2.3** — the thundering-herd explanation for why jitter exists at all.
- **2.1** — the breaker as one of five agent-safety layers, enabling *graceful degradation* (switch to
  conservative mode) rather than crashing.
- **5.2** — breaker states in Step Functions plus load shedding: deliberately drop low-priority traffic to
  protect emergency queries.

### G2. Timeouts — three unrelated senses [8]
**Owner: 2.5** — the alignment rule: **Model < Lambda ≤ API Gateway < Client**, and the failure if you get it
wrong — the gateway returns a generic 504 while Lambda keeps burning resources invisibly with nobody listening.
**Also appears in:**
- **2.4** — sizing by job weight: 4–5 s for real-time clinical queries (fail fast to a fallback beats a
  spinner), 15–30 s for simple inference, up to 120 s for complex generation.
- **2.2** — the trap that catches people: a 100 GB+ model takes 20–40 minutes to download and load, while
  default container health checks give it 5–10. Raise them to 60 minutes or the deploy "fails" on a healthy model.
- **2.1** — Lambda's hard 15-minute ceiling repurposed as an agent stopping condition.
- **1.3** — why orchestration moves to Step Functions: a long Transcribe job breaches Lambda's 15 minutes.
- **1.1** — AppSync's 30-second integration limit, worked around with an async mutation that returns a
  `conversationId` immediately and streams over a subscription.

### G3. Throttling & concurrency [10, domains 2–5]
**Owner: 2.4** — the multi-level hierarchy (account ~10,000 RPS → stage 1,000–5,000 → route 50–500) and why
route-level matters most: a heavy reasoning model may only take 50 RPS while a classifier takes 500, so limits
must be derived from downstream model capacity, not picked arbitrarily.
**Also appears in:**
- **4.2** — Step Functions Map `MaxConcurrency` so 100 requests run 10 at a time and wait safely in state
  instead of triggering 429s and a retry storm.
- **2.3** — API Gateway usage plans and API keys per internal team, for isolation *and* chargeback; reserved
  vs provisioned Lambda concurrency.
- **4.1** — reserved concurrency as a ceiling protecting Bedrock's limits; provisioned concurrency billed
  even when idle.
- **3.1** — rate limiting reframed as a security control against brute-force prompt probing.

### G4. Queues — three different motives [several]
**Owner: 4.1** — the cost motive, stated cleanly: without a queue you provision for peak and idle most of the
time; with one you provision for *average* and let peaks drain. The cost is latency during bursts.
**Also appears in:**
- **2.2** — the *reliability* motive: requests are never rejected during a spike, they wait. SageMaker
  Asynchronous endpoints do this natively, writing output to S3 and notifying via SNS.
- **4.2** — the *throughput* motive: micro-batching, plus priority queues (or SQS message attributes) so ER
  requests are never stuck behind routine documentation.
- **2.3** — ordering: SQS FIFO with Message Group IDs keyed on customer id, preserving sequence *within* a
  customer while processing customers in parallel. And Amazon MQ instead of SQS when the legacy system
  already speaks JMS/AMQP — it exists so you don't have to rewrite the legacy side.
- **5.2** — load shedding under severe load.

### G5. Streaming [several, domains 1/2/4]
**Owner: 4.2** — the conceptual split that makes it make sense: **actual** latency (8 s, unchanged) vs
**perceived** latency (first token at ~500 ms instead of 8,000 ms). Called the most cost-effective way to cut
perceived latency without touching infrastructure or model choice.
**Also appears in:**
- **2.4** — the wire-level detail: SSE vs WebSockets, and why SSE usually wins for LLM output (the client has
  nothing to send back) — plus its superpower, `Last-Event-ID`, which resumes from event 48 instead of
  regenerating everything. Buffer 5–20 chunks, flush on size, on 100–500 ms, or on a semantic boundary so
  half-sentences never render.
- **2.5** — progressive rendering at 50–200 ms, WebSocket idle timeouts of 10–30 minutes with ping/pong
  heartbeats, and the correct `text/event-stream` content type.
- **2.5 (accessibility)** — the part nothing else covers: streamed tokens are invisible to screen readers
  unless the container is an **ARIA live region**. Without it, a blind user hears nothing at all.
- **1.1** — AppSync GraphQL subscriptions for token streaming.
- **4.3** — the reality check: the server logged 2.0 s, CloudWatch RUM says the user's screen finished at 5.0 s.

### G6. X-Ray [7, domains 1/2/4/5]
**Owner: 2.4** — subsegments (preprocessing / invocation / postprocessing), annotations as filterable tags
(model name, complexity, quality score) so you can later ask for "every slow cardiology request", and
percentiles: p50 is the typical user, p99 is the worst 1% that averages hide.
**Also appears in:**
- **2.3** — sampling rules, because tracing 100% is prohibitively expensive: 5% of normal requests, 100% of
  slow ones and errors.
- **4.2** — profiling *prompt shapes* — which token lengths and tool sequences actually cost latency.
- **2.5** — GenAI annotations answering "why do prompts over 4,000 tokens lag disproportionately?"
- **5.2** — the best single argument for tracing: it proved the bottleneck was the **auth middleware**, not
  the model, which every dashboard had been blaming.
- **4.3** — trace maps integrated into CloudWatch, and per-step latency inside agent runs.

### G7. Step Functions — the same service doing twelve unrelated jobs [14, all 5 domains]
No single owner. This is the most-repeated service in the notes, and the reason it's confusing is that each
task uses it for something different. The whole entry *is* the disambiguation:
- **1.3** — parallel multimodal processing, chosen specifically because Lambda's 15-minute cap can't hold a
  long Transcribe job.
- **1.5** — parallel execution of decomposed sub-queries.
- **1.6** — conversation state machine, clarification loops, and the parallel edge-case test runner.
- **2.1** — the macro-deterministic shell around an agent's ReAct loop; stopping conditions; wait tokens.
- **2.3** — Parallel state for concurrent fraud checks; Map state applying one workflow to 1,000 transactions.
- **2.4** — Choice states selecting a model from content.
- **2.5** — parallel document sections, plus hybrid orchestration with EventBridge (Step Functions is
  *declarative* — what runs; EventBridge is *reactive* — when it starts).
- **3.1** — risk-based branching, red-team test orchestration, and the incident escalation workflow.
- **3.3** — governance approval gates before a model reaches production.
- **4.1** — automating prompt-compression test iterations.
- **4.2** — parallel independent calls, and Map `MaxConcurrency` as throttle protection.
- **5.1** — scheduled daily evaluation runs.
- **5.2** — a sliding window over long records; circuit breaker states.

### G8. CloudWatch — what it's actually doing in each task [16, all 5 domains]
Same treatment as G7. The service is everywhere; the *job* differs:
- **1.3** — data quality *trend* (validation pass rate drifting 94% → 91% → 87% means an upstream export
  format changed).
- **1.2** — operational metrics + SNS alarms (JSON parse failures >1% in an hour pages the on-call).
- **1.6** — human escalation rate as the early-warning signal: escalations spike while error rates stay flat,
  which means the model is failing *quietly*.
- **2.2 / 4.1** — the two rules of thumb: GPU utilization ~20% means the instance is oversized; cache hit
  rate under 5% means the cache isn't earning its keep.
- **2.3** — composite alarms combining latency AND low confidence AND error rate, to kill false positives.
- **4.2** — latency percentiles, and **CloudWatch Evidently** for experimentation — distinguished from
  AppConfig, which is for feature flags and rollouts.
- **4.3** — the deepest treatment: unified GenAI views, anomaly detection with *seasonality* awareness
  (Monday-morning peaks aren't incidents), custom metrics for hallucination and relevance, RUM for
  client-side truth, and the AgentCore tab.
- **3.3** — metric filters extracting governance signals from log streams.
- **5.2** — Logs Insights queries for prompt-confusion signatures: unsubstituted `{{variables}}` leaking to
  users, the model discussing the template instead of the question, acknowledged instruction conflicts.

### G9. Evaluation — what gets measured, and where [several, all 5 domains]
**Owner: 5.1** — the four core quality dimensions (relevance, factual accuracy, consistency, fluency) and
their independence — fluent but wrong, accurate but irrelevant; domain dimensions on top (compliance, tone);
LLM-as-a-judge with the hard constraint **never let a model judge itself** (self-preference bias); Bedrock's
four eval features including BYOI; and the dual-phase RAG split — **retrieve-only vs retrieve-and-generate** —
which is the root-cause isolator: if retrieval passes and the answer is still wrong, the generator
hallucinated, not the vector search.
**Also appears in:**
- **1.2** — the three-tier gate (automatic → judge → human), BLEU vs ROUGE (precision vs recall) and their
  shared fatal flaw: both are text overlap, so "patient has chest pain" scores well against "patient does
  not have chest pain". Plus the exam trap: **latency and cost are not part of model evaluation** — that's a
  load test, not an eval.
- **3.1** — the same machinery pointed at *safety* instead of accuracy, with custom metrics because generic
  toxicity scoring can't see domain hazards like unlicensed investment advice.
- **3.4** — the judge used for *fairness*, plus judge-bias mitigation: explicit rubrics, ensemble judging,
  human calibration.
- **4.3** — the judge used to make hallucination an alarmable number against a golden set.
- **4.1** — evaluation extended with price-to-performance: cost per accuracy point, where 89% at a fifth of
  the price beats 94%.

### G10. A/B vs canary vs blue-green vs feature flags [4]
**Owner: 5.1** — the purpose split: A/B testing is for *comparative analysis* (which variant is better),
canary is for *risk mitigation* (ship safely by degrees).
**Also appears in:**
- **2.4** — the mechanics: 5–10% to the candidate, 90–95% on baseline, then statistical significance testing.
- **4.2** — the AWS-service distinction worth memorizing: **CloudWatch Evidently** for quantitative
  experimentation, **AppConfig** for feature flags and progressive rollout.
- **3.3** — blue/green traffic shift as *automated remediation* when a drift alarm fires.
- **5.2** — A/B across prompt variants rather than models.

### G11. Hallucination — the full control stack [10, domains 1/3/4/5]
**Owner: 3.1** — the five-layer accuracy pipeline, and the honest admission at layer 1: **grounding reduces
hallucination but does not eliminate it**. Then semantic similarity to check the answer came from the
sources, confidence routing, schema bounds, and the structural answer — **text-to-SQL**, where the model
writes a query instead of an answer, a Lambda validates it's SELECT-only against whitelisted tables, and the
number comes from the database, making hallucination *structurally impossible*.
**Also appears in:**
- **1.1 / 1.6** — contextual grounding checks as a guardrail feature, mathematically verifying the response
  is supported by retrieved chunks.
- **4.3** — turning it into a metric, since nothing ships hallucination detection out of the box.
- **5.1** — retrieve-only vs end-to-end evaluation to assign blame (see G9).
- **2.5 / 4.3** — the retrieval log as the decisive evidence: if the retrieved chunks were already
  irrelevant, the model behaved correctly and the RAG tier is at fault. This stops teams tuning the wrong
  component during an incident.
- **1.2** — why automated metrics alone can't catch it (the negation flip above).

### G12. Fine-tuning vs prompting vs RAG [12, all 5 domains]
**Owner: 1.2** — LoRA mechanics: the base model's weights are frozen, a <1% trainable adapter is attached,
and adapters are modular and swappable without rebuilding anything. Plus the comparison that drives the
choice — few-shot prompting wastes tokens on every single call and risks instruction drift, while fine-tuning
bakes the behavior in and leaves the prompt short. 100–300 curated JSONL pairs.
**Also appears in:**
- **2.2** — the deployment consequence: keep one base model resident in VRAM and swap LoRA adapters in
  seconds; and Custom Model Import economics — your fine-tuned model with *serverless pay-per-token* pricing
  instead of a 24/7 GPU endpoint bill.
- **1.4 / 1.5** — the same instinct applied to *embedding* models, which need domain adaptation for the same
  reason.
- **3.3** — the legal dimension: per-vendor licensing that records whether a dataset may be used for
  pre-training, fine-tuning, or RAG prompt injection at all.

### G13. Stateless models & conversation state [several]
**Owner: 1.6** — models remember nothing, so state is infrastructure: DynamoDB with PK `session_id` /
SK `timestamp`, and the governance twist — a 90-day **TTL is a regulatory retention control**, not database
hygiene. It enforces GDPR-style deletion with no cron job.
**Also appears in:**
- **1.3** — the hybrid sliding window: compress old turns to a summary, keep recent turns verbatim, and avoid
  token bloat.
- **2.1** — the three-tier memory hierarchy (see D1).
- **2.5** — prompt-chaining reduction when the window is the constraint.
- **5.2** — a sliding window via Step Functions across a long medical record.
- **2.3** — the same DynamoDB+TTL mechanism used for something unrelated: **idempotency** keys.

### G14. Idempotency [2]
**Owner: 2.3** — external webhooks are at-least-once, so duplicates *will* arrive. Event IDs are checked
against DynamoDB with TTL and the cached result is returned instead of re-invoking the model — otherwise the
email sends twice and you're billed twice.
**Also appears in:**
- **2.4** — the same bug from the other direction: an SQS visibility timeout set too short means SQS assumes
  the worker died while it's still mid-inference, re-delivers the message, and you pay for the call twice.

### G15. Correlation IDs & blame attribution [several]
**Owner: 4.3** — correlation IDs binding request → model invocation → business event, and the insight that
makes them matter: **HTTP 200 is not success**. If the user clicks "talk to a human" immediately after the
answer, the request succeeded and the system failed. Same logic as tool success vs tool *effectiveness* —
200 OK with an empty JSON body is 100% success and 0% effectiveness.
**Also appears in:**
- **3.3** — correlation IDs for *audit* traceability across distributed services.
- **2.5** — full-lifecycle logging with retrieval results as the critical audit point.
- **5.2** — the symptom→tool table that operationalizes all of this.

### G16. Business metrics vs technical metrics [several]
**Owner: 4.3** — the table and the framing: latency 2.0 s → 1.8 s matters to engineers; "escalation rate down
20%" is what proves ROI. Dashboards split by audience — CloudWatch for SREs, QuickSight for executives.
**Also appears in:**
- **5.1** — business outcome alignment: map latency, per-token cost and hallucination rate to first-contact
  resolution and support cost.
- **2.5** — the discipline: baseline *before* release, then statistical significance testing, so you don't
  credit the model for noise.
- **1.6** — human escalation rate as the single best early-warning indicator.

### G17. The GenAI Gateway [1 task, but it's where everything converges]
**Owner: 2.3** — the problem it solves, stated as a list of what breaks without it: spend is untrackable,
guardrails get applied inconsistently or forgotten, there's no unified audit trail, and swapping models means
every team rewrites code. One gateway centralizes access control, per-team rate limits and chargeback,
uniform guardrails nobody can bypass, routing and fallback, shared caching, and audit logging — and becomes
an abstraction layer so a model swap is a gateway change, not 12 team migrations.
**Why it's in this index:** it's the single place where Domain 2's integration, Domain 3's guardrails and
audit, and Domain 4's cost tracking and caching are all the *same* component. Good anchor for the
whole-exam map.

---

## Notes on gaps and judgement calls

1. **Concepts with no clean owner.** G7 (Step Functions) and G8 (CloudWatch) have no owner by design — the
   entry *is* the disambiguation. B2 (confidence thresholds) is the shakiest assignment: 2.1 has the cleanest
   ladder, but 3.4 explains where the number comes from. Worth your call.
2. **1.1 is a summary task.** Its notes are a cheat sheet spanning all of Domain 1, so it rarely owns a
   concept but corroborates many. It mostly contributes exam *rules* (the OpenSearch-Serverless-for-SaaS rule
   is its best).
3. **4.1 owns a lot** (chunking-for-cost, caching, cascading, batching, provisioned break-even, token
   economics). That's correct — Domain 4 is only 12% of the exam but 4.1's notes are the densest on money.
4. **Things that appear once and are owned trivially** — not included as cross-cutting entries, but they
   belong on their task page: Global Accelerator (1.1), Amazon MQ (2.3), Inferentia/Trainium (4.2),
   Audit Manager + GenAI Best Practices Framework (3.4), Kinesis feedback streaming (5.1), attention
   visualization (2.5, theoretical only — Bedrock doesn't expose attention weights).
5. **Six concept diagrams** proposed earlier map onto these entries: the RAG request path (A1–A7),
   chunk→embed→index→retrieve (A1–A3), the guardrail sandwich (E1–E2), the cascade/routing ladder (B1–B2),
   retry→backoff→breaker (G1), and the eval loop (G9–G10).
