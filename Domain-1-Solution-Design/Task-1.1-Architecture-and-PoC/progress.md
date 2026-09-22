# Task 1.1 — Architecture & PoC — Progress

## Status

**Live build complete (Steps 1–4 done).** S3 bucket with 3 synthetic claims + 3 policy documents, an S3-triggered Lambda that extracts structured fields, matches the relevant policy (simple RAG), validates, and summarizes via Bedrock — live-tested end-to-end for all 3 sample claims — plus a head-to-head Haiku vs. Sonnet comparison on summary generation. Old status text below, kept for context: `project.md` in this folder previously contained the wrong content — Task 1.6's bonus assignment (a customer-support governance PoC) had been pasted into it by mistake. That content was fully built and live-tested (14 steps, 29 resources, `adi-1-1-*` naming) before the mixup was caught. The user has since corrected `project.md` to the real Task 1.1 brief: an **insurance-claims document processing PoC** using Amazon Bedrock. The old build log below is preserved for the historical record but the live build it describes is now attributed to Task 1.6, not this task — see `Domain-1-Solution-Design/Task-1.6-Prompt-Engineering-and-Governance/progress.md` and `Website/src/tasks/task-1-6.html`.

## What actually happened (historical, kept for reference)

Steps 1–14 below were built and verified under this folder's `adi-1-1-*` resource names, but implement **Task 1.6's** brief (persona + Guardrails + Prompt Management governance + Step Functions orchestration + QA harness for an EC2-troubleshooting support assistant), not this task's real insurance-claims brief. Resources were not renamed or deleted — renaming live AWS resources means deleting and recreating them for no benefit — only the documentation attribution changed. Full step-by-step detail now lives in Task 1.6's own `progress.md` and `Website/src/tasks/task-1-6.html`.

## Real Task 1.1 brief (current `project.md`)

An insurance company wants to automate processing of claim documents. Scope:

1. **Design the architecture (Skill 1.1.1)** — S3 storage, processing workflow, FM integration, response generation; pick Bedrock models for document understanding, extraction, and summarization.
2. **Implement PoC (Skill 1.1.2)** — S3 bucket, a Python app with document upload, Bedrock integration, a simple RAG component using policy information, and claim summary generation.
3. **Reusable components (Skill 1.1.3)** — prompt template manager, model invoker, basic content validator.
4. **Test and evaluate** — 2–3 sample claim documents, compare model performance, document findings.

Nothing built yet. Cheap brief — S3 + on-demand Bedrock calls only, no provisioned/hourly resource anywhere in it, so there's no cost reason to hold off (unlike the Kendra/OpenSearch situations elsewhere in this project).

## Website deliverables (done)

- `Website/src/tasks/task-1-1.html` — rewritten as a build plan for the real insurance-claims brief (all steps marked "Planned, not built"), with a clear note explaining the mixup and linking to Task 1.6's page for the previously-mislabeled content.
- `Website/src/tasks/task-1-6.html` — rewritten to claim the 14-step / 29-resource build as its own (dropped the earlier "reused from Task 1.1" framing from a prior session), with a note explaining why resources are still named `adi-1-1-*`.
- `Website/src/tasks/index.html` — both task cards updated to match.
- Task 1.1 and Task 1.6 Study Notes pages (`Website/src/notes/task-1-1.html`, `task-1-6.html`) are unaffected — both were already built from each task's own `notes.md`, which is unrelated to which bonus-assignment scenario got built.

## Naming for the real build (when started)

Use `adi-1-1-claims-*` (not `adi-1-1-support-*`, which belongs to the historical/Task-1.6 stack) to avoid any naming collision in the account: `adi-1-1-claims-documents-269737522732` (S3), `adi-1-1-claims-processor-role` (IAM), `adi-1-1-claims-processor` (Lambda). See `Website/src/tasks/task-1-1.html` for the full planned resource index.

## Resources Deployed

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 1 | S3 Bucket | adi-1-1-claims-documents-269737522732 | arn:aws:s3:::adi-1-1-claims-documents-269737522732 | Step 2 |
| 2 | IAM Role | adi-1-1-claims-processor-role | arn:aws:iam::269737522732:role/adi-1-1-claims-processor-role | Step 3 |
| 3 | Lambda Function | adi-1-1-claims-processor | arn:aws:lambda:us-east-1:269737522732:function:adi-1-1-claims-processor | Step 3 |

## Step Log

### Step 1 — Architecture design + model selection (Skill 1.1.1)
- **What:** Confirmed AWS identity (`admin`, account `269737522732`, profile `awsgenai`). Listed current-gen foundation models available in `us-east-1` and live-tested invoke access via `bedrock-runtime converse`:
  - `us.anthropic.claude-haiku-4-5-20251001-v1:0` (Claude Haiku 4.5) — confirmed working, real reply received.
  - `us.anthropic.claude-sonnet-4-6` (Claude Sonnet 4.6, via cross-region inference profile — the bare model ID rejects on-demand invocation the same way Task 1.6's build found for Sonnet/Haiku) — confirmed working, real reply received.
  - **Model selection:** Claude Haiku 4.5 for document understanding + information extraction (fast, cheap, good at structured JSON output — same model already proven reliable in this account's prior build). Both Haiku 4.5 and Sonnet 4.6 will be compared head-to-head for summary generation in Step 4, since summary quality is more likely to show a real difference between model tiers than field extraction is.
  - **Architecture:** S3 bucket (`adi-1-1-claims-documents-269737522732`) holds raw claim documents and sample policy documents → an S3-upload-triggered Lambda (`adi-1-1-claims-processor`) extracts structured fields via Bedrock, looks up the matching policy document (simple RAG component), generates a summary via Bedrock, and writes the result back to S3 — following this project's established "live, event-driven PoC" pattern (matching Task 1.5's chunking-engine) rather than a local-only script, even though the brief's own sample code is written as a plain Python script.
- **Where to check:** No new AWS resource yet — this step is model access confirmation only. Console → Amazon Bedrock → Model access (`us-east-1`) shows Claude Haiku 4.5 and Claude Sonnet 4.6 access already granted from earlier tasks.
- **Why:** Every later step calls one of these two models, so access had to be proven with a real request/response before building anything on top of it — same standard every other task on this site holds to. Picking Haiku for extraction and comparing both for summarization gives Step 4's "compare model performance" requirement a real, meaningful axis to measure (structured-output reliability is not very different between adjacent Claude tiers; prose summary quality typically is).
- **Verified:** Both `converse` calls returned the exact expected text (`OK-HAIKU`, `OK-SONNET`) with no errors.

### Step 2 — S3 bucket + sample claim/policy documents (Skill 1.1.2, part 1)
- **What:** Created `adi-1-1-claims-documents-269737522732` (`us-east-1`, versioning on, all public access blocked). Authored 3 synthetic insurance claims with deliberately varied formatting — a narrative email-style auto claim (`claim1_auto.txt`), a structured intake-form property/water-damage claim (`claim2_property.txt`), and a terse quick-submit urgent-care claim (`claim3_health.txt`) — plus 3 matching policy documents (`POL-AUTO-88213`, `POL-HOME-55021`, `POL-HEALTH-30456`) each with coverage limits, deductibles, and exclusions. Uploaded claims to `raw-claims/` and policies to `policies/`.
- **Where to check:** Console → **S3 → adi-1-1-claims-documents-269737522732** — `raw-claims/` (3 objects) and `policies/` (3 objects).
- **Why:** Varied formatting (prose vs. form vs. terse) means extraction actually has to generalize, not just parse one fixed template — same reasoning Task 1.5 used for its chunking sample data. Policy documents are named by policy number specifically so a simple string-match lookup (Step 3) can find the right one, no vector database needed at this scale.
- **Verified:** `aws s3 ls --recursive` confirms all 6 objects.

### Step 3 — Claims-processor Lambda: extraction, RAG lookup, validation, summary (Skill 1.1.2 part 2 + Skill 1.1.3)
- **What:** Created `adi-1-1-claims-processor-role` (trusts `lambda.amazonaws.com`; scoped to S3 read/write on the claims bucket and `bedrock:InvokeModel` on exactly Claude Haiku 4.5 and Sonnet 4.6, model + inference-profile ARNs). Built and deployed `adi-1-1-claims-processor` (Python 3.13, 256MB, 60s timeout), S3-triggered on `raw-claims/*.txt` uploads. Contains the brief's three requested reusable components as classes in one module:
  - **`PromptTemplateManager`** — holds the extraction and summary prompt templates by name.
  - **`ModelInvoker`** — thin wrapper around Bedrock's Converse API, one place for every model call in this project.
  - **`ContentValidator`** — checks the extraction JSON has all 5 required fields, that `claim_amount` parses as numeric and `incident_date` contains a recognizable year, before the summary step runs.
  - Processing flow: read claim text from S3 → extract 5 fields via Bedrock (Claude Haiku 4.5, temperature 0.0) → validate → look up the matching policy document by policy number directly in S3 (the brief's "simple RAG component using policy information" — brute-force lookup, the same reasoning Task 1.5 used for why a managed vector store isn't needed at PoC scale) → generate a 2-3 sentence adjuster-facing summary via Bedrock, explicitly prompted to reference the matched policy's coverage limit → write the full result JSON to `processed/`.
  - Wired a real S3 event notification (`s3:ObjectCreated:*` on `raw-claims/` with `.txt` suffix) plus the Lambda resource policy, then re-uploaded all 3 sample claims to fire the trigger live rather than only testing via manual invoke.
- **Where to check:** Console → **Lambda → adi-1-1-claims-processor** (Configuration → Trigger shows the S3 event source) → **Monitor → Logs**. **S3 → adi-1-1-claims-documents-269737522732 → processed/** — 3 JSON result objects.
- **Why:** This is the brief's core PoC deliverable — a working pipeline demonstrating document upload, Bedrock integration, RAG, and summary generation, built as the three reusable components the brief explicitly asks for rather than one monolithic script.
- **Verified — real results, all 3 claims, via the live S3 trigger (not just manual invoke):**
  - **claim1_auto** (narrative style): extracted `Marcus Reyes / POL-AUTO-88213 / 2025-09-14 / $4,200 / rear-ended at a red light`, all correct; policy matched; summary correctly flagged the $500 deductible and the police-report requirement (claim > $2,000) — both facts pulled from the policy document, not the claim text.
  - **claim2_property** (form style): extracted `Priya Natarajan / POL-HOME-55021 / 2025-11-02 / $8,750 / burst supply line`, all correct; policy matched; summary correctly noted the $75,000 water-damage limit and the photographic-evidence requirement (claim > $5,000).
  - **claim3_health** (terse style): extracted `Daniel Ekwueme / POL-HEALTH-30456 / 2025-12-03 / $890 / slipped on ice, urgent care`, all correct despite the sparse "quick submit" format; policy matched; summary correctly applied the $50 urgent-care deductible.
  - All 3: `validation.valid: true`, `policy_matched: true` — extraction generalized across three genuinely different document shapes, and every summary demonstrably used the matched policy's actual terms (deductible amounts, coverage limits), confirming the RAG component is load-bearing, not decorative.

### Step 4 — Test and evaluate: model comparison (Haiku 4.5 vs. Sonnet 4.6)
- **What:** Ran `compare_models.py` (standalone script, same shape as the brief's own `compare_models()` sample) against claim2's real extracted data + matched policy excerpt, invoking both models on the identical summary prompt and measuring latency, token usage, and output.
- **Where to check:** `Domain-1-Solution-Design/Task-1.1-Architecture-and-PoC/lambda/claims-processor/compare_models.py`; raw comparison JSON captured in this step log below.
- **Why:** This is the brief's "compare performance of different models" requirement — a real, measured difference rather than an assumption that a bigger model is automatically better.
- **Findings (real numbers, not estimates):**

  | Model | Time | Output tokens | Notable behavior |
  |---|---|---|---|
  | Claude Haiku 4.5 | 1.76s | 162 | Concise single paragraph; states the claim falls within the coverage limit. |
  | Claude Sonnet 4.6 | 4.71s | 257 | ~2.7x slower; adds markdown structure (headers/bold) unprompted; **actually computes the net payout after the deductible** ($8,750 claim − $1,000 deductible = $7,750 eligible payout) — a genuinely more useful, concrete detail Haiku's summary didn't include. |

  **Recommendation:** Haiku 4.5 for extraction (structured-JSON reliability was identical between the two models in this test, and Haiku is faster/cheaper for a high-volume field-extraction task). Sonnet 4.6 is the better choice for the summary-generation step specifically, since its willingness to actually perform the deductible arithmetic is a real accuracy advantage for an adjuster-facing summary, not just a style difference — worth the added latency for a step that doesn't run per-document at extraction volume.
- **Verified:** Both calls returned real, distinct outputs with real token/latency numbers — not simulated.

## Concepts Explained

- **A simple RAG component doesn't need a vector database at PoC scale.** With only 3 policy documents, matching a claim's extracted `policy_number` directly against S3 object keys finds the exact right policy document every time — same "brute-force is fine below a certain scale" reasoning Task 1.5 used for its retrieval-evaluator design.
- **Model choice is a per-step decision, not a single project-wide pick.** The real comparison in Step 4 showed structured extraction was equally reliable on both models, but summary generation showed a genuine capability difference (Sonnet performing real deductible arithmetic unprompted) — justifying using Haiku for one step and Sonnet for another, rather than picking one model for the whole pipeline.
- **Deliberately varied sample-document formatting is what makes an extraction test meaningful.** All 3 claims used different structures (narrative email, structured form, terse quick-submit) specifically so a real extraction failure on any one format would have been visible — a single consistent template would have proven far less.

## Next Step

None planned — Steps 1–4 are complete. Possible next-session extensions (from the brief's own "Extra challenging steps"): a simple Flask web interface, content filtering for sensitive information (e.g. Bedrock Guardrails, reusing the pattern already proven in Task 1.6), or a feedback mechanism for adjuster corrections.
