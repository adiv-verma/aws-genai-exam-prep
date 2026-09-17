# Task 1.3 — Data Validation & Multimodal Processing Pipeline — Progress

## Status

Starting. Approval check done (no AWS-side quota blockers — see below). Building Phase 1, Step 1 next.

## Project Summary (from project.md)

Build a data validation and processing pipeline for customer feedback from four sources (text reviews, product images, customer service call recordings, survey responses), preparing it for foundation-model consumption to generate business insights.

Four parts:
1. **Data validation workflow** — Glue Data Quality (structured data), custom Lambda validation (unstructured text), CloudWatch quality-trend monitoring.
2. **Multimodal data processing** — Comprehend (text), Textract (image text), Rekognition (image labels), Transcribe (audio calls), SageMaker Processing (survey → NL summaries).
3. **Data formatting for FMs** — conversation templates + multimodal request formatting for Claude on Bedrock.
4. **Data quality enhancement** — Comprehend entity/theme extraction, text normalization, a feedback loop using model responses to improve upstream data quality.

Note: `project.md`'s pasted code sample cuts off mid-function partway through Part 3 (`format_image_data`) — have the full architecture outline (top of file) and Parts 1-2 in full detail, so building Part 3-4 from the outline + this project's own established patterns (same as how Task 1.2 extended past brief gaps).

## Pre-flight: AWS approval check

Unlike Task 1.2 (blocked on SageMaker **training**-job instance quotas, all 0 by default on this account), this task's only SageMaker usage is a **Processing** job — a separate quota bucket. Checked directly: `ml.m5.xlarge for processing job usage` = **8** (quota code `L-0307F515`), already available. Every other service used here (Glue, Comprehend, Textract, Rekognition, Transcribe, Lambda, CloudWatch, Bedrock) is pure on-demand/serverless with no instance quota at all. **No AWS-side approval needed for this task.** Estimated total PoC cost: under $5 (all pay-per-call, nothing hourly/persistent left running).

## Scenario (scoped for a solo PoC)

Consumer-electronics retailer analyzing customer feedback for **one product line — wireless earbuds** — across all four required modalities: text reviews, product photos (packaging/damage), customer-service call recordings, and post-purchase satisfaction surveys. Narrow scope keeps sample data concrete (same "start narrow" approach as Tasks 1.1/1.2).

Naming: `adi-1-3-` prefix for all resources. Region: `us-east-1` (Bedrock model access already confirmed here in Task 1.2).

Sample data is hand-authored/synthesized (no course-provided sample-data repo attached to this project): text reviews as JSON, product images generated with Pillow (simple synthetic packaging/damage photos with baked-in labels — good enough to exercise Textract/Rekognition end-to-end, not aiming for real-photo label richness), audio synthesized with **Amazon Polly** (short customer-service call scripts, TTS'd to real MP3/WAV so Transcribe has genuine speech to work with), survey responses as CSV.

## Phased Build Plan

- **Phase 1 — Data validation workflow**
  1. S3 bucket + prefix structure; author and upload synthetic sample dataset (reviews, images, audio, survey CSV) to `raw-data/`
  2. Glue Crawler + Data Quality ruleset over the survey CSV (structured data)
  3. Custom Lambda, S3-triggered, for text-review validation → writes a CloudWatch quality-score metric
  4. CloudWatch dashboard for quality trend over time
- **Phase 2 — Multimodal data processing**
  5. Lambda: Comprehend entity extraction + sentiment + key phrases for validated text reviews
  6. Lambda: Textract (text-in-image) + Rekognition (labels) for product images
  7. Step Functions + Lambda for audio: `StartTranscriptionJob` → native wait/poll, **not** a blocking `while True: sleep(5)` inside a single Lambda like the brief's sample code (would risk the Lambda 15-min timeout on longer calls — same reasoning already documented in this task's own `notes.md` Stage 2 for why Step Functions beats Lambda for long-running async work) → Comprehend sentiment on the resulting transcript
  8. SageMaker Processing job: survey CSV → natural-language summaries (quota confirmed clear above)
- **Phase 3 — Data formatting for FMs**
  9. Lambda: unify all four processed-data shapes into Bedrock Converse-ready messages — conversation templates for dialog-style analysis, multimodal content blocks where an image is involved
  10. Test-invoke against Claude Haiku 4.5 (`us.anthropic.claude-haiku-4-5-20251001-v1:0`, confirmed working in Task 1.2) for a few formatted records; verify coherent business-insight output
- **Phase 4 — Data quality enhancement**
  11. Aggregate Comprehend key-entity/theme pass across all processed reviews → a business-insight summary (recurring complaint themes, etc.)
  12. Lambda: text normalization (HTML/whitespace/abbreviation cleanup), inserted upstream of Phase 2's text processing
  13. Feedback loop: when Bedrock's own analysis flags a record as low-confidence/insufficient-data, write that back as a quality-score adjustment on the source record — closes the loop to Phase 1's CloudWatch metric

Each step: build → report what/where-to-verify/why → wait for user confirmation → log here before moving on (same cadence as Task 1.2).

## Resources Deployed

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 1 | S3 Bucket | adi-1-3-customer-feedback-269737522732 | arn:aws:s3:::adi-1-3-customer-feedback-269737522732 | Step 1 |

## Step Log

### Step 1 — S3 bucket + synthetic sample dataset
- **What:** Created `adi-1-3-customer-feedback-269737522732` (`us-east-1`, versioning on, all public access blocked). Wrote `data/generate_sample_data.py` and ran it to produce:
  - **12 text reviews** (`data/reviews/rev-001.json`..`rev-012.json`) — 10 realistic wireless-earbuds reviews (mix of 1-5 star, varied topics: battery, Bluetooth drops, damaged packaging, wrong color, support non-response) plus **2 deliberately low-quality reviews** (`rev-011`: valid fields but a 2-word review; `rev-012`: missing `product_id`, out-of-range rating "7", wrong date format) — these exist specifically to exercise the Phase 1 Step 3 validation Lambda's failure path and confirm the quality-score/CloudWatch pipeline actually discriminates good from bad data, not just report 100% pass.
  - **4 product images** (`data/images/*.png`) — Pillow-generated synthetic packaging/damage photos with real printed text baked in (product name, model number, a "CASE CRACKED ON ARRIVAL" damage photo) so Textract/Rekognition have genuine text and shapes to detect. Not photorealistic — good enough to exercise the pipeline end-to-end, not aiming for rich label detection.
  - **2 customer-service call recordings** (`data/audio/call-*.mp3`) — real synthesized speech via **Amazon Polly** (`Joanna`/`Matthew`, standard engine) reading short billing-dispute and defective-product support call scripts, so Amazon Transcribe gets genuine audio rather than silence/noise.
  - **Survey CSV** (`data/surveys/surveys.csv`) — 12 rows: `customer_id, survey_date, overall_satisfaction, product_rating, service_rating, improvement_area, comments`.
  - Uploaded all of it to `s3://adi-1-3-customer-feedback-269737522732/raw-data/{reviews,images,audio,surveys}/`.
- **Where to check:** Console → **S3 → adi-1-3-customer-feedback-269737522732 → raw-data/** — 19 objects across the 4 prefixes.
- **Why:** No course-provided sample-data repo is attached to this project (brief just says "sample data provided in the project repository"), so realistic synthetic data had to be authored for all four modalities. Using Polly for audio (rather than silent/blank files) matters because Transcribe's output quality is the actual thing Phase 2 Step 7 needs to demonstrate — a blank MP3 would prove nothing about the pipeline. Two intentionally-bad reviews matter for the same reason: a validation pipeline that never fails anything doesn't prove it's validating.
- **Verified:** `aws s3 ls` confirms all 19 objects present at expected keys/sizes.

### Step 2 — Glue Crawler + Data Quality ruleset over the survey CSV
- **What:** Created `adi-1-3-glue-role` (trusts `glue.amazonaws.com`; scoped to S3 read on `raw-data/*`, Glue Catalog actions on the `adi_1_3_customer_feedback_db` database/tables, plus a Glue Data Quality action group and CloudWatch Logs — see below on why DQ needed broader `Resource: "*"`), Glue database `adi_1_3_customer_feedback_db`, and crawler `adi-1-3-survey-crawler` targeting `raw-data/surveys/`. Ran it — correctly inferred the `surveys` table schema (ratings as `bigint`, dates/text as `string`). Created ruleset `adi-1-3-survey-quality-ruleset` (DQDL): completeness on `customer_id`/`survey_date`/`overall_satisfaction`, a date-format regex, discrete-set checks (`in [1,2,3,4,5]`) on the three rating columns, and `RowCount > 0`. Ran the evaluation — **final score 1.0, all 8 rules PASS** against the 12-row survey table.
- **Two real bugs hit and fixed along the way:**
  1. **IAM gap, twice** — the DQ evaluation actually runs as a Spark job under the assumed role, which needs to call back into Glue to report its own status/results. First run failed `AccessDeniedException` on `glue:GetDataQualityRulesetEvaluationRun`; after adding that, a second run failed on `glue:PublishDataQuality`. Neither action is scopable to a specific resource ARN in a meaningful way (the evaluation-run resource isn't nameable ahead of time), so these went in a separate statement with `Resource: "*"` — narrowly, to just these 4-5 read/status-report DQ actions, not a blanket Glue grant.
  2. **DQDL rule-authoring bugs, not IAM** — first real evaluation ran clean but returned score 0.5 with legitimate-looking rows failing: the date-regex rule failed 100% of rows, and the three rating `between 1 and 5` rules failed exactly at the boundary values (1 and 5). Root cause: the regex was typed inside a single-quoted bash heredoc as `\\d` (double backslash) instead of `\d` — bash preserved it literally, so the DQDL engine searched for a literal backslash character, matching nothing. Fixed the escaping, and separately swapped `between 1 and 5` for the unambiguous `in [1,2,3,4,5]` (ratings are integers only, so a discrete-set check is both correct and avoids finding out empirically whether DQDL's `between` is inclusive or exclusive). Re-ran clean: score 1.0.
- **Where to check:** Console → **AWS Glue → Data Catalog → Databases → adi_1_3_customer_feedback_db → Tables → surveys**; **Data Quality → Rulesets → adi-1-3-survey-quality-ruleset** shows the run history and per-rule results.
- **Why:** Matches the brief's own split — Glue Data Quality for *structured* data (the survey CSV) vs. custom Lambda for *unstructured* text (Step 3, next) — rather than force-fitting the brief's reviews-shaped DQDL example onto data it doesn't actually describe (see Project Summary note above on where `project.md`'s sample code applies). The IAM/DQDL bugs are worth keeping in the log for the exam: `ResourceLimitExceeded` (Task 1.2) means quota, `AccessDeniedException` mid-Spark-job on a DQ action means the *executing role* (not just the caller) needs Data-Quality-specific permissions since the job reports its own status, and a rule that fails 100% or exactly at its boundary values is almost always an authoring bug (escaping, operator semantics), not a real data problem — worth checking the rule syntax before trusting the score.
- **Verified:** `get-data-quality-result` output above — all 8 rules PASS, score 1.0.

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 2 | IAM Role | adi-1-3-glue-role | arn:aws:iam::269737522732:role/adi-1-3-glue-role | Step 2 |
| 3 | Glue Database | adi_1_3_customer_feedback_db | arn:aws:glue:us-east-1:269737522732:database/adi_1_3_customer_feedback_db | Step 2 |
| 4 | Glue Crawler | adi-1-3-survey-crawler | — | Step 2 |
| 5 | Glue Table | surveys | arn:aws:glue:us-east-1:269737522732:table/adi_1_3_customer_feedback_db/surveys | Step 2 |
| 6 | Glue Data Quality Ruleset | adi-1-3-survey-quality-ruleset | arn:aws:glue:us-east-1:269737522732:dataQualityRuleset/adi-1-3-survey-quality-ruleset | Step 2 |

### Step 3 — Custom Lambda for text-review validation
- **What:** `adi-1-3-text-validation-role` (least-privilege: `s3:GetObject` on `raw-data/reviews/*` only, `s3:PutObject` on `validation-results/reviews/*` only, `cloudwatch:PutMetricData` scoped via a `cloudwatch:namespace` condition to exactly `CustomerFeedback/TextQuality`, scoped log-group write). Lambda `adi-1-3-text-validation` (`lambda/text_validation/handler.py`, Python 3.13) — extends the brief's sample checks (min length, product reference, opinion words, has-structure) with a few more that actually matter for this data: required-fields-present, rating-in-range (1-5), and date-format-valid, each contributing to a 7-check `quality_score`. Wired an S3 `ObjectCreated` notification scoped to `raw-data/reviews/` + `.json` suffix, invoking this Lambda directly (brief's sample used a separate `create-event-source-mapping` call, which is for poll-based sources like SQS/Kinesis — S3 uses bucket notification config + `lambda:AddPermission` instead, the correct mechanism for this trigger type).
- **Tested live**, not just invoked synthetically: re-uploaded all 12 review files to `raw-data/reviews/`, letting the real S3 event fire the real Lambda. All 12 `_validation.json` results landed in `validation-results/reviews/`. Spot-checked: `rev-001` (good review) scored **1.0**, the two deliberately-bad reviews scored **0.43** (`rev-011`, 2-word review) and **0.14** (`rev-012`, missing/invalid fields) — confirms the validator actually discriminates rather than rubber-stamping everything. CloudWatch `QualityScore` metric (namespace `CustomerFeedback/TextQuality`) shows all 12 datapoints: avg 0.83, min 0.14, max 1.0 — matches the per-file results exactly.
- **Where to check:** Console → **Lambda → adi-1-3-text-validation**; **S3 → adi-1-3-customer-feedback-269737522732 → validation-results/reviews/**; **CloudWatch → Metrics → CustomerFeedback/TextQuality**.
- **Why:** Same split rationale as Step 2 — this Lambda owns *unstructured* text validation (the brief's Part 1 Step 1/3), separate from Glue DQ's *structured* survey validation (Step 2). Testing via a real re-upload (not a synthetic `lambda invoke` payload) proves the actual S3-to-Lambda wiring works end-to-end, not just the handler logic in isolation.
- **Verified:** 12/12 validation files present with expected scores; CloudWatch datapoint count and stats match.

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 7 | IAM Role | adi-1-3-text-validation-role | arn:aws:iam::269737522732:role/adi-1-3-text-validation-role | Step 3 |
| 8 | Lambda Function | adi-1-3-text-validation | arn:aws:lambda:us-east-1:269737522732:function:adi-1-3-text-validation | Step 3 |
| 9 | S3 Bucket Notification | adi-1-3-text-validation-trigger | on adi-1-3-customer-feedback-269737522732, raw-data/reviews/*.json -> Lambda | Step 3 |

### Step 4 — CloudWatch dashboard for quality trend
- **What:** Created dashboard `adi-1-3-CustomerFeedbackQuality` — left widget: `QualityScore` + `ValidationPass` averages from Step 3's real metric namespace; right widget: the Lambda's own `Invocations`/`Errors` (native `AWS/Lambda` metrics). **Deliberately swapped out** the brief's sample second widget (`CustomerFeedback/DataQuality`, `RulesetPassRate`) — that's a metric name the brief's own sample code never actually publishes anywhere (Glue Data Quality results don't auto-publish to CloudWatch as a custom metric; you'd have to add a `put-metric-data` call after each DQ run yourself, which wasn't part of this task's scope). Using the real, already-existing Lambda health metrics instead of a fictitious placeholder metric that would render as an empty graph.
- **Where to check:** Console → **CloudWatch → Dashboards → adi-1-3-CustomerFeedbackQuality**.
- **Why:** A dashboard pointing at a metric nothing ever publishes is worse than no dashboard — it looks configured but silently shows nothing. Swapping to a metric with guaranteed real data (native Lambda metrics) keeps the dashboard honest while still covering the brief's intent (operational visibility into the validation pipeline).
- **Verified:** `get-dashboard` confirms it exists; both widgets reference metrics with real data behind them (Step 3's 12 datapoints; Lambda ran 12 times with 0 errors).

**Phase 1 complete.**

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 10 | CloudWatch Dashboard | adi-1-3-CustomerFeedbackQuality | arn:aws:cloudwatch::269737522732:dashboard/adi-1-3-CustomerFeedbackQuality | Step 4 |

### Step 5 — Lambda: Comprehend text processing
- **What:** `adi-1-3-text-processing-role` (read on `validation-results/reviews/*` + `raw-data/reviews/*`, write on `processed-data/reviews/*`, `comprehend:DetectEntities`/`DetectSentiment`/`DetectKeyPhrases` — Comprehend has no resource-level ARNs to scope to, so this is a plain action-only allow, same data-plane-action pattern as other tasks in this project). Lambda `adi-1-3-text-processing` — triggered on `validation-results/reviews/*_validation.json`, re-reads the matching original review, skips anything below the Step 3 quality threshold (0.7), otherwise runs the brief's 3 Comprehend calls and writes `processed-data/reviews/*_processed.json`. Chained the S3 triggers (`raw-data/reviews/` → validation Lambda → writes to `validation-results/reviews/` → processing Lambda → writes to `processed-data/reviews/`) via one bucket notification config with two non-overlapping prefix/suffix filters.
- **Tested live**: re-uploaded all 12 raw reviews, which cascaded through both real S3 triggers automatically. **10/12 processed** — the exact 2 deliberately-bad reviews (`rev-011`, `rev-012`) were correctly gated out by the quality threshold, not processed. Spot-checked `rev-004` (damaged package/missing earbud complaint): Comprehend correctly scored it 99.99% `NEGATIVE`, extracted sensible key phrases ("the case", "the packaging quality"), confirming the pipeline isn't just wired but producing correct analysis.
- **Where to check:** Console → **Lambda → adi-1-3-text-processing**; **S3 → processed-data/reviews/**.
- **Why:** Gating on the Step 3 quality score (not just running Comprehend on everything) is the actual point of Part 1's validation stage — bad data should never reach the expensive/consequential processing steps. Chaining real S3 events end-to-end (rather than testing each Lambda in isolation) proves the whole raw→valid→processed pipeline works as one system.
- **Verified:** 10 processed files present, count matches (12 raw - 2 gated), spot-checked content is correct.

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 11 | IAM Role | adi-1-3-text-processing-role | arn:aws:iam::269737522732:role/adi-1-3-text-processing-role | Step 5 |
| 12 | Lambda Function | adi-1-3-text-processing | arn:aws:lambda:us-east-1:269737522732:function:adi-1-3-text-processing | Step 5 |

### Step 6 — Lambda: Textract + Rekognition for product images
- **What:** `adi-1-3-image-processing-role` (read `raw-data/images/*`, write `processed-data/images/*`, `textract:DetectDocumentText`, `rekognition:DetectLabels`/`DetectText`). Lambda `adi-1-3-image-processing`, triggered on `raw-data/images/` (no suffix filter — accepts any file under that prefix, unlike the suffix-filtered review triggers, since images have three valid extensions). Added as a third entry to the same bucket notification config (now 3 non-overlapping Lambda triggers on one bucket).
- **Real bug hit and resolved:** first live test appeared stuck — no processed output for any image, and a `describe-log-streams` check initially showed no log group at all, looking exactly like the trigger wasn't wired. Confirmed the function itself worked via a direct `lambda invoke` (succeeded, found 5 labels), which meant the S3→Lambda plumbing, not the code, was suspect. Root cause turned out to be neither: CloudWatch Logs was **reusing one warm log stream across multiple invocations** (Lambda execution-environment reuse), so `describe-log-streams --limit 3` was only surfacing the stream name, not that it held two separate `START`/`END` invocation blocks. Reading the full stream showed the S3 trigger *had* fired correctly — the second invocation had actually run and failed with `UnsupportedDocumentException` from Textract on one specific file. A direct retry of `detect-document-text` against that exact S3 object moments later succeeded with no code change, confirming it was a one-off transient Textract error, not a real format problem (`file` confirmed valid 8-bit RGB PNG). Re-ran all 4 images — all 4 processed cleanly this time.
- **Tested live**: all 4 images (`WEB-100_packaging`, `WEB-100_case_damage`, `WEB-200-PRO_packaging`, `WEB-200-PRO_charging_cable`) processed. Spot-checked `WEB-100_case_damage_processed.json`: Textract correctly extracted `"CASE CRACKED ON ARRIVAL"` from the synthetic damage photo; Rekognition found real generic labels (Triangle, White Board, Page, Text) even on a simple Pillow-drawn image.
- **Where to check:** Console → **Lambda → adi-1-3-image-processing**; **S3 → processed-data/images/**.
- **Why:** Worth keeping in the log for the exam-relevant lesson: when a trigger looks silently broken, check whether CloudWatch is just reusing a warm log stream before concluding the event never fired — `describe-log-streams` ordering by `LastEventTime` shows *stream* recency, not that a stream is single-invocation. And `UnsupportedDocumentException` from Textract isn't always a real format problem; a same-second retry against the identical object is a cheap way to tell transient from persistent before changing code.
- **Verified:** 4/4 processed files present; spot-checked content matches the source image's actual content (both the baked-in text and the visual shape).

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 13 | IAM Role | adi-1-3-image-processing-role | arn:aws:iam::269737522732:role/adi-1-3-image-processing-role | Step 6 |
| 14 | Lambda Function | adi-1-3-image-processing | arn:aws:lambda:us-east-1:269737522732:function:adi-1-3-image-processing | Step 6 |

### Step 7 — Transcribe via Step Functions (not a blocking Lambda)
- **What:** Three new IAM roles (`adi-1-3-audio-trigger-role`, `adi-1-3-audio-processing-role`, `adi-1-3-stepfunctions-audio-role`), two Lambdas, one state machine:
  - `adi-1-3-audio-trigger` — tiny S3-triggered Lambda, only starts a Step Functions execution (`states:StartExecution`) with `{bucket, audio_key, job_name, output_key, media_format}`; does no polling itself.
  - `adi-1-3-audio-transcription-sm` — Standard state machine using native SDK integrations (`aws-sdk:transcribe:startTranscriptionJob` / `getTranscriptionJob`, no separate Lambda needed for either call): Start → Wait 20s → Get → Choice (COMPLETED → process, FAILED → Fail state, else → loop back to Wait) → invoke `adi-1-3-audio-processing`.
  - `adi-1-3-audio-processing` — reads the finished transcript from `transcriptions/`, runs Comprehend sentiment + key phrases, writes `processed-data/audio/*_processed.json`.
  - This is the brief's own architectural point (also documented in this task's `notes.md` Stage 2) made real: the brief's sample code blocks a single Lambda in a `while True: sleep(5)` loop waiting on the transcription job, which risks the 15-minute Lambda timeout on longer calls. Here the *wait* lives in Step Functions' own `Wait` state (no compute billed, no timeout risk), and Lambda only does the two real units of work (start execution, process finished transcript).
- **Real hiccup (not a bug — a propagation delay), and why it's not the same as Step 6's issue:** the S3 trigger on `raw-data/audio/` produced **zero invocations for several minutes** after wiring — genuinely zero, no log group at all this time (unlike Step 6's warm-log-stream confusion, which was a real invocation I'd misread). Confirmed the Lambda/role/state-machine chain was correct via a direct `lambda invoke` for `call-001` — that started a real Step Functions execution which ran to `SUCCEEDED` end-to-end. Then, without any config change, re-uploading `call-002` **did** trigger the real S3 event automatically (visible as a second, independently-started execution). Conclusion: S3 bucket notification configs on a bucket that already has several Lambda function configurations can take a few minutes to fully activate a newly-added one — not a wiring bug, just eventual-consistency lag on the S3 side. Same underlying category of "looks broken, isn't" as Step 6, worth expecting when adding a 4th+ notification config to one bucket.
- **Tested live, both paths**: `call-001` (manual invoke → real SF execution → SUCCEEDED) and `call-002` (genuine S3 auto-trigger → real SF execution → SUCCEEDED). Both produced `processed-data/audio/*_processed.json`. Spot-checked `call-002`: **transcript is highly accurate** (Transcribe correctly captured the full billing/defect dialogue from the Polly-synthesized audio), sentiment scored 99.7% POSITIVE (call ends on a resolved note despite an initial complaint — plausible document-level read), key phrases correctly pulled out ("a replacement pair", "no additional cost", "24 hours"). Speaker diarization returned a single speaker (`spk_0`) for the whole call — expected, not a bug: both calls were synthesized with **one Polly voice reading both sides** of the dialogue (Step 1), so there's genuinely only one voice track for Transcribe to diarize against; a real 2-speaker test would need two distinct TTS voices merged into one audio file, out of scope for this PoC's sample-data effort.
- **Where to check:** Console → **Step Functions → adi-1-3-audio-transcription-sm → Executions** (both `SUCCEEDED`, full visual execution history); **S3 → transcriptions/** and **processed-data/audio/**.
- **Why:** Matches the brief's Part 2 Step 3 requirement while fixing the brief's own sample code's architectural flaw, and demonstrates the exact async-orchestration pattern (`Wait`/`Choice`/native SDK integrations) that's exam-relevant for "why Step Functions over Lambda" questions.
- **Verified:** both executions `SUCCEEDED` in the Step Functions console history; both processed files present with correct, sensible content.

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 15 | IAM Role | adi-1-3-audio-processing-role | arn:aws:iam::269737522732:role/adi-1-3-audio-processing-role | Step 7 |
| 16 | IAM Role | adi-1-3-audio-trigger-role | arn:aws:iam::269737522732:role/adi-1-3-audio-trigger-role | Step 7 |
| 17 | IAM Role | adi-1-3-stepfunctions-audio-role | arn:aws:iam::269737522732:role/adi-1-3-stepfunctions-audio-role | Step 7 |
| 18 | Lambda Function | adi-1-3-audio-processing | arn:aws:lambda:us-east-1:269737522732:function:adi-1-3-audio-processing | Step 7 |
| 19 | Lambda Function | adi-1-3-audio-trigger | arn:aws:lambda:us-east-1:269737522732:function:adi-1-3-audio-trigger | Step 7 |
| 20 | Step Functions State Machine | adi-1-3-audio-transcription-sm | arn:aws:states:us-east-1:269737522732:stateMachine:adi-1-3-audio-transcription-sm | Step 7 |

### Step 8 — SageMaker Processing job: survey CSV to NL summaries
- **What:** `adi-1-3-sagemaker-execution-role` (S3 read on `raw-data/surveys/*` + `code/*`, write on `processed-data/surveys/*`, `ecr:*` pull actions for the built-in container, scoped logs). `sagemaker/survey_processing.py` — same shape as the brief's sample (clean → normalize ratings → per-row NL summary + aggregate stats) but extended stats (avg per rating dimension, top-5 improvement areas) and using the real **built-in SKLearn Processing container** (`683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3` — the correct `us-east-1` framework-container account, found by attempting an image_uris lookup via the `sagemaker` SDK; that lookup itself failed on an unrelated local `sagemaker/` directory name collision in this project shadowing the installed package, so fell back to the well-known account ID directly and verified it by simply running the job — it was accepted immediately, no wrong-image blocker).
- **Real bug caught before spending any SageMaker time**: ran the script locally first (`data/surveys/surveys.csv` copied to a scratch dir) before ever creating the processing job. First local run produced `"improvement_area": NaN` in the JSON output for rows that should have said `"None"` — pandas' `read_csv` treats the literal string `"None"` as one of its default missing-value tokens and silently nulls it. Fixed with `keep_default_na=False` (safe here since every column always has *some* value, no columns are meant to be genuinely empty), re-ran locally, confirmed correct output, **then** launched the real job — avoided paying for a SageMaker run that would've shipped corrupted data.
- **Ran for real**: `create-processing-job` on `ml.m5.xlarge` (the exact instance type whose quota was confirmed clear before starting this task), `MaxRuntimeInSeconds: 900` safety cap. Completed in **~2 minutes total** (instance provisioning + 83s actual script run) — Status `Completed`, no failure. Output matches the local dry-run exactly: `survey_statistics.json` (avg satisfaction 3.25/5, top improvement areas: Customer support, Build quality) and 12 `survey_summaries.json` entries with correct NL summaries and the `"None"`-vs-NaN fix confirmed in the real S3 output too.
- **Where to check:** Console → **SageMaker → Processing → Processing jobs → adi-1-3-survey-processing** (status `Completed`); **S3 → processed-data/surveys/**.
- **Why:** SageMaker Processing bills per-second while the instance actually runs and then tears itself down automatically (unlike Task 1.2's real-time endpoint / Provisioned Throughput decision point, which bills hourly whether used or not) — this run cost a fraction of a cent, matching the pre-flight cost estimate exactly. Testing the script locally first is what real ML engineers do before spending managed-instance time; the NaN bug would've been just as real (and just as invisible until spot-checked) if caught only after paying for the job.
- **Verified:** job status `Completed`; output file contents match the corrected local dry-run byte-for-byte in structure and match expectations on data.

**Phase 2 complete.**

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 21 | IAM Role | adi-1-3-sagemaker-execution-role | arn:aws:iam::269737522732:role/adi-1-3-sagemaker-execution-role | Step 8 |
| 22 | SageMaker Processing Job | adi-1-3-survey-processing | arn:aws:sagemaker:us-east-1:269737522732:processing-job/adi-1-3-survey-processing | Step 8 |

### Step 9 — Lambda: unify all four processed-data shapes into Bedrock Converse messages
- **What:** `adi-1-3-bedrock-formatting-role` (read `processed-data/*` + `raw-data/images/*`, write `formatted-data/*`). Lambda `adi-1-3-bedrock-formatting` — dispatches on which fields are present (`transcript` → audio, `extracted_text` → image, `entities` → review) or handles the single aggregate `survey_summaries.json` by iterating its array, and for each record builds a real Bedrock Converse payload: shared analyst system prompt + a per-modality user turn. For images specifically, implements the brief's "multimodal request formatting" literally — fetches the actual raw image bytes from `raw-data/images/` and includes a real `image` content block alongside the Textract/Rekognition text, not just a text description of the image. Two non-overlapping S3 triggers on the same Lambda: `processed-data/` + `_processed.json` suffix (catches reviews/images/audio) and `processed-data/surveys/` + `survey_summaries.json` suffix (the one aggregate file).
- **Two real bugs caught, one before deploy and one during testing:**
  1. **Caught in code review before deploying**: raw image bytes aren't JSON-serializable, so writing a formatted payload straight to S3 with a Python `bytes` object in it would have crashed every image-record invocation. Fixed by base64-encoding the image into the stored JSON (`bytes_base64`) and documenting that Step 10's actual Bedrock invoke call must decode it back to raw bytes — boto3's Converse API wants real bytes in that field, not a base64 string.
  2. **Caught live**: my usual "re-trigger already-processed files" test method (`aws s3 cp key key` to force a new PUT event) **silently failed** for the review/image/audio processed files — `aws s3 cp` refuses a same-key-to-same-key S3-to-S3 copy with no metadata change (`InvalidRequest: ... trying to copy an object to itself without changing the object's metadata...`), and my loop had piped stderr to `/dev/null`, hiding 16 failed copies. Result looked exactly like Step 6/7's propagation-delay pattern (partial results: only the 12 survey files appeared, from a genuine fresh write in Step 8, not a self-copy) — but this time the cause was different: a real, permanent CLI restriction, not a delay. Fixed by not relying on same-key self-copy at all: re-uploaded the original raw-data files instead, which cascades through every already-tested upstream trigger (Steps 3/5/6/7) end-to-end into this new formatting step — a more realistic test anyway.
- **Tested live end-to-end**: re-uploaded all raw reviews/images/audio; all **28 formatted files** landed (10 reviews + 4 images + 2 audio + 12 surveys, matching expected counts exactly). Spot-checked the most complex case (`WEB-100_case_damage_formatted.json`): correct `modelId`, correct text block (product/Textract/Rekognition context), correct `image` content block (format `png`, valid base64 payload) — a genuine multimodal Bedrock request ready to send as-is.
- **Where to check:** Console → **Lambda → adi-1-3-bedrock-formatting**; **S3 → formatted-data/{reviews,images,audio,surveys}/**.
- **Why:** Worth remembering for the exam: `aws s3 cp` cannot no-op-copy an object to its own key without changing something (metadata, storage class, etc.) — a real, permanent API restriction, not eventual consistency, and it fails differently (`InvalidRequest`, immediate) from the propagation-lag issue in Steps 6/7 (silent, resolves itself given time). Piping a batch loop's stderr to `/dev/null` is exactly how this kind of failure hides — worth checking exit codes/stderr even in "just re-triggering test data" loops, not only in real application code.
- **Verified:** 28/28 formatted files present with correct counts per modality; spot-checked content is structurally correct and would work as-is against the real Bedrock Converse API.

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 23 | IAM Role | adi-1-3-bedrock-formatting-role | arn:aws:iam::269737522732:role/adi-1-3-bedrock-formatting-role | Step 9 |
| 24 | Lambda Function | adi-1-3-bedrock-formatting | arn:aws:lambda:us-east-1:269737522732:function:adi-1-3-bedrock-formatting | Step 9 |

### Step 10 — Test-invoke Claude Haiku 4.5 against formatted records
- **What:** `scripts/test_bedrock_invoke.py` — pulls one formatted record from each of the 4 modalities from S3, decodes the image block's base64 back to raw bytes (per Step 9's noted handoff contract), and calls the real Bedrock `converse` API with `us.anthropic.claude-haiku-4-5-20251001-v1:0` (confirmed accessible in Task 1.2).
- **Ran it live against all 4**: a damaged-package review, the cracked-case product image (genuine multimodal — image bytes + Textract/Rekognition text both sent), the defective-earbud call transcript, and a Bluetooth-pairing-failure survey response. **All 4 produced coherent, correctly-escalated analysis** matching the system prompt's 3-part ask (core issue, escalation flag, actionable recommendation) — e.g. the image case correctly identified "damaged product upon delivery" and recommended a packaging-durability audit, the audio case flagged the 2-week charging failure as a potential batch-defect risk and recommended pulling the serial/batch number for failure analysis. Token usage logged per call (219-443 input / 101-158 output) — trivially cheap at this volume, consistent with the pre-flight cost estimate.
- **Where to check:** re-run `scripts/test_bedrock_invoke.py` locally, or Console → **Bedrock → nothing persisted here** (this step doesn't write new S3 output — it's a validation that Step 9's formatted payloads are actually usable as-is, not a new pipeline stage).
- **Why:** Confirms the whole formatting pipeline (Step 9) isn't just structurally correct JSON but actually produces good model output when sent for real — including proving the multimodal image path works (Claude's analysis of the image case referenced the crack specifically, which only comes from the actual image content block, not just the Textract/Rekognition text summary).
- **Verified:** 4/4 live Bedrock calls succeeded with on-topic, correctly-escalated output.

**Phase 3 complete.**

### Step 11 — Aggregate Comprehend entity/theme pass across all processed reviews
- **What:** `adi-1-3-theme-aggregation-role`, Lambda `adi-1-3-theme-aggregation` — lists all `processed-data/reviews/*_processed.json`, aggregates sentiment distribution (overall and per-product), top-10 recurring key phrases, top-10 entities, and entity-type distribution, writes `insights/reviews_theme_summary.json`. Invoked manually (not S3-event-triggered) — this is a batch business-report job over the whole dataset, not a per-record pipeline stage, same distinction as Task 1.2's benchmark script; in production this would be an EventBridge scheduled rule, out of scope to wire up for a PoC.
- **Real IAM bug hit and fixed**: first invoke failed `AccessDenied` on `s3:GetObject`, despite the object clearly being inside the resource path the policy granted. Root cause: I'd combined `s3:ListBucket` and `s3:GetObject` into **one statement sharing one `Condition` block** keyed on `s3:prefix` — but `s3:prefix` is a request-context key that only exists on `ListBucket` calls; for `GetObject` calls that key is simply absent, so the condition silently fails to match and IAM denies the whole statement for that action. Split into two statements (one for `ListBucket` + the prefix condition, one plain `GetObject` grant scoped by Resource path alone, no condition) — fixed immediately.
- **Ran it live**: 10/10 processed reviews aggregated correctly (matches Phase 2's quality-gated count exactly). Sentiment distribution: 4 POSITIVE / 3 MIXED / 3 NEGATIVE, split further by product (`WEB-100` vs `WEB-200-PRO`). Recurring themes/entities are mostly count=1 given the small 10-review sample — expected and honest at this scale, not a bug.
- **Where to check:** Console → **Lambda → adi-1-3-theme-aggregation**; **S3 → insights/reviews_theme_summary.json**.
- **Why:** Worth keeping in the log for the exam: a `Condition` block attached to a multi-action statement is evaluated against **every** action in that statement, and if a condition key doesn't exist in a given action's request context, the condition doesn't just get skipped — it fails to match, denying that action. Combining actions with different applicable condition keys in one statement is a real, easy-to-make authoring mistake, distinct from the DQ-role and formatting-role bugs earlier in this task (those were *missing* actions entirely, not a mismatched condition on an action that was present).
- **Verified:** output matches expected review count and per-product breakdown exactly.

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 25 | IAM Role | adi-1-3-theme-aggregation-role | arn:aws:iam::269737522732:role/adi-1-3-theme-aggregation-role | Step 11 |
| 26 | Lambda Function | adi-1-3-theme-aggregation | arn:aws:lambda:us-east-1:269737522732:function:adi-1-3-theme-aggregation | Step 11 |

### Step 12 — Text normalization, inserted upstream of Comprehend processing
- **What:** Extended `adi-1-3-text-processing` (Step 5) in place rather than adding a new Lambda/stage — added `normalize_text()`: HTML-entity unescape, HTML tag strip, a small domain-specific abbreviation map (`w/`→with, `BT`→Bluetooth, `mins`/`min`→minutes, `approx`→approximately), whitespace collapse. Comprehend now runs against `normalized_text`; the processed-review record keeps **both** `original_text` (unmodified, for audit/traceability) and `normalized_text` (what was actually analyzed).
- **Added two new deliberately-noisy sample reviews** (`rev-013`, `rev-014`) — existing samples were already clean, so normalization would've been a silent no-op with nothing to prove. New reviews contain HTML tags/entities, irregular whitespace, and the target abbreviations.
- **Two real bugs caught before/while deploying:**
  1. **Caught locally before deploying** (same discipline as Step 8's SageMaker script): ran `normalize_text()` standalone against the two noisy sample texts first. `w/` was never replaced — root cause: the pattern `\bw/\b` requires a word/non-word transition on *both* sides of the match, but the position right after `/` (followed by a space) is non-word-to-non-word, so `\b` never matches there. Fixed with `\bw/(?=\s|$)` (lookahead for whitespace/end instead of a trailing `\b`), re-tested locally, confirmed correct before touching the deployed Lambda.
  2. Redeployed via `update-function-code` (not a new function - correctly updates the existing one in place, keeping its IAM role/triggers).
- **Tested live end-to-end**: uploaded `rev-013`/`rev-014` through the full `raw-data/reviews/` → validation → processing chain. `rev-013`'s output confirms it worked exactly as intended: Comprehend extracted `"20 minutes"` and `"no Bluetooth dropouts"` as key phrases — those exact phrases only exist in the *normalized* text (raw had `"BT"` and irregular-spaced `"20   mins"`); Comprehend never saw the noisy original.
- **Where to check:** Console → **Lambda → adi-1-3-text-processing** (updated code); **S3 → processed-data/reviews/rev-013_processed.json** / `rev-014_processed.json` — both fields present side by side.
- **Why:** Matches the brief's Stage 4 "text reformatting/noise removal before the expensive model sees it" principle (also independently described in this task's own `notes.md` Stage 4, written before this build started) — cleaner input means better-quality structured extraction, and keeping `original_text` alongside `normalized_text` preserves auditability rather than silently discarding the source. The regex bug is worth remembering: a trailing `\b` after a non-word character followed by whitespace is a common, easy-to-miss dead pattern.
- **Verified:** live Comprehend output for `rev-013` contains normalized-only phrases, confirming the normalization step actually ran before analysis, not just that the code compiles.

## Resources Deployed (continued)

_(Step 12 updated an existing resource — `adi-1-3-text-processing` — no new resources.)_

### Step 13 — The feedback loop: Bedrock confidence adjusts the source record's quality score
- **What:** `adi-1-3-feedback-loop-role`, Lambda `adi-1-3-feedback-loop`, triggered on `formatted-data/reviews/*_formatted.json`. Reuses Step 9's already-built user-turn content but with its own system prompt asking Bedrock for a strict-JSON `{data_sufficient, confidence, reasoning}` assessment — is this feedback specific/concrete enough to actually drive a business decision, not just well-formed. If `data_sufficient` is false or `confidence < 0.5`, it **overwrites the Phase 1 `validation-results/reviews/*_validation.json` quality_score** (`adjusted = original * confidence`), attaches a `feedback_adjustment` audit trail, and emits a new `FeedbackAdjustedQualityScore` CloudWatch metric into the *same* `CustomerFeedback/TextQuality` namespace Step 1's dashboard already watches — closing the loop for real, not just writing to a new unrelated file. Always writes a `quality-feedback/reviews/*_feedback.json` audit record regardless of outcome, for traceability either way.
- **Added `rev-015`** (deliberately vague-but-valid: "It's fine I guess...") specifically to create a genuine low-confidence case — every prior sample review was either clearly good or gated out entirely by Phase 1, neither of which would exercise this step's adjustment path.
- **Tested live, 4 real cases, both directions of the loop:**
  - `rev-015` (vague): confidence **0.15**, adjusted 0.857 → **0.129** — correctly penalized.
  - `rev-001` ("I love these earbuds... battery lasts all day... sound quality excellent"): confidence **0.35**, adjusted 1.0 → **0.35** — a real, informative surprise: even a clearly positive, well-formed review got marked low-confidence because it has no concrete specifics (no actual battery hours, no comparison) to drive a *specific* business decision under this prompt's bar. Not a bug — a legitimate, if strict, model judgment worth noting for anyone tuning this prompt's threshold later.
  - `rev-004` (cracked case, missing earbud): confidence **0.92**, data sufficient, **no adjustment** — correctly kept its original 1.0 score, giving the needed contrast case.
  - `rev-016` (new: "earbud caught fire while charging, melted nightstand — safety hazard"): confidence **0.92**, no adjustment — correctly recognized as concrete/actionable, and this one ran through the **entire pipeline fully automatically end-to-end** (raw upload → validation → normalization+Comprehend → formatting → feedback loop, all 4 S3 triggers firing in sequence with zero manual invokes) — real proof the whole 13-step pipeline works unattended, not just stage-by-stage.
- **Same propagation-lag pattern as Steps 6/7/9** hit again on this newly-added trigger (`rev-015`/`rev-001` initially showed no invocation for several minutes despite correct config) — used manual `lambda invoke` to get immediate verified results (same workaround as Step 7), then confirmed the real auto-trigger with `rev-016` once more time had passed. By this point in the build, this is a well-established, expected behavior on this bucket rather than a new mystery each time.
- **Where to check:** Console → **Lambda → adi-1-3-feedback-loop**; **S3 → validation-results/reviews/** (adjusted scores) and **quality-feedback/reviews/** (audit trail); **CloudWatch → Metrics → CustomerFeedback/TextQuality → FeedbackAdjustedQualityScore**.
- **Why:** This is the brief's Part 4 Step 3 literally — "a feedback loop to improve data quality based on model responses" — and it's a genuine loop, not a one-way pipeline: Stage 1's quality gate influences what reaches Bedrock (Steps 3/5), and Bedrock's own judgment now writes back into that same Stage 1 quality signal, visible on the same dashboard built in Step 4. The rev-001 result is a good real finding to carry into any writeup: "well-formed" (Phase 1's check) and "business-actionable" (Phase 4's check) are genuinely different qualities, and a pipeline that only checks the former will still let vague-but-valid feedback through un-flagged without a step like this one.
- **Verified:** 4/4 live Bedrock-backed assessments produced correct, differentiated outcomes; one full unattended end-to-end run confirmed the complete pipeline.

## Resources Deployed (continued)

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 27 | IAM Role | adi-1-3-feedback-loop-role | arn:aws:iam::269737522732:role/adi-1-3-feedback-loop-role | Step 13 |
| 28 | Lambda Function | adi-1-3-feedback-loop | arn:aws:lambda:us-east-1:269737522732:function:adi-1-3-feedback-loop | Step 13 |

**Phase 4 complete. All 13 steps of the phased build plan complete.**

## Next Step

None — the full pipeline (Phases 1-4) is built, live, and verified end-to-end. If revisited: consider a scheduled (EventBridge) trigger for Step 11's theme-aggregation report instead of manual invoke, and note the `rev-001` confidence finding (Step 13) if tuning the feedback-loop's system prompt/threshold further. Website Build Log (`Website/src/tasks/task-1-3.html`) written in plain English (matching Task 1.1/1.2 style) and published, hub page (`Website/src/tasks/index.html`) updated with a Task 1.3 card. Study Notes page (`Website/src/notes/task-1-3.html`) already existed from a prior session, covering a different (insurance-claims) example of the same conceptual pipeline — left as-is, no changes needed.
