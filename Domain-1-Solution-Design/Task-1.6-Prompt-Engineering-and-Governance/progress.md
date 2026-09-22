# Task 1.6 — Prompt Engineering Strategies and Governance — Progress

## Status

**Phases 1–5 complete (Steps 1–14 done).** Scenario: **EC2 instance troubleshooting customer support assistant**. Region: `us-east-1`. Model: **Claude Haiku 4.5** via inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0`. All resources are named with the `adi-1-1-` prefix — see **Naming note** below for why. QA test harness (5/5 pass) plus a full CloudWatch dashboard + 5 alarms (including 2 custom-metric regression alarms built on EMF instrumentation). Next: Bedrock Prompt Flows (the brief's "complex prompt system design" component), JSON Schema response validation, and a custom-trained Comprehend classifier — all planned, not yet built (see **Next Step**).

## Naming note — why resources are prefixed adi-1-1-, not adi-1-6-

This build was originally started under the Task 1.1 folder, because an earlier session's `project.md` for Task 1.1 had Task 1.6's bonus-assignment content pasted into it by mistake. Everything below was built and live-tested against that (correct, for this task) content before the mixup was caught. Task 1.1's real brief (an insurance-claims document processing PoC) is unrelated and untouched — see `Domain-1-Solution-Design/Task-1.1-Architecture-and-PoC/progress.md`. Resources were not renamed or recreated (that would mean deleting and rebuilding for no real benefit) — only the documentation and task attribution were corrected. This is genuinely Task 1.6's own live build.

## Project Summary (from project.md)

Build a customer support AI assistant (AWS troubleshooting bot) that demonstrates:
1. **Model instruction framework** — persona via Bedrock Prompt Management + Guardrails (block credential sharing, future-feature commitments, competitor talk).
2. **Prompt management and governance** — parameterized templates, versioning in S3, approval workflow, CloudTrail/CloudWatch tracking, RBAC.
3. **Quality assurance system** — Lambda validators, Step Functions test workflows, regression monitoring.
4. **Iterative prompt enhancement** — feedback loop, chain-of-thought patterns.
5. **Complex prompt system design** — Bedrock Prompt Flows with branching, fallback, human handoff.

Implementation steps (per brief): Architecture setup → Development → Testing → Refinement.

## Phased Build Plan (scoped for a solo PoC)

**Scenario:** single support domain = EC2 troubleshooting, to keep templates/tests concrete (brief recommends starting narrow).

- **Phase 1 — Foundation**
  1. Confirm Bedrock model access (Claude) in `us-east-1`
  2. `adi-1-1-prompt-templates` S3 bucket (versioned) — prompt template storage
  3. `adi-1-1-support-conversations` DynamoDB table — conversation history (+ TTL)
  4. `adi-1-1-bedrock-lambda-role` IAM role — least-privilege Lambda → Bedrock/DynamoDB/S3
- **Phase 2 — Prompt Management & governance**
  5. Base persona prompt in Bedrock Prompt Management (role boundaries, tone, response format)
  6. 2–3 parameterized scenario templates (diagnostic, clarification, escalation)
  7. CloudTrail trail + CloudWatch Logs group for prompt invocation tracking
  8. IAM policy demonstrating RBAC for template modification (separate prompt-editor role)
- **Phase 3 — Guardrails**
  9. Bedrock Guardrail: content filters (credential/secret sharing), denied topics (future feature commitments, competitor discussion), PII, contextual grounding
- **Phase 4 — Orchestration**
  10. Lambda: capture query + intent/confidence detection
  11. Lambda: invoke model (prompt template + guardrail applied) + output validation
  12. Step Functions state machine: capture → detect intent → choice (clarify if low confidence) → generate → validate → respond
- **Phase 5 — QA & testing**
  13. Lambda validators + Step Functions test harness for edge cases (angry customer, vague request, prompt-injection attempt)
  14. CloudWatch dashboard/alarms for regression signals (latency, throttles, validation failures)
- **Phase 6 — New for this task, not yet built**
  15. JSON Schema (draft-07) response validation Lambda — required `disclaimer` field, structural enforcement beyond the lightweight checks in Step 11
  16. Bedrock Prompt Flows — deterministic multi-step flow (pre-process → classify → branch → generate → post-process), reusing the persona/guardrail resources already live above
  17. Custom-trained Amazon Comprehend classifier via async batch jobs (not a persistent real-time endpoint, which would bill ~$0.50/hr / ~$360/mo even idle)

Also flagged and **not planned at all**: Amazon Kendra (`project.md`'s own "Consider Amazon Kendra..." line) — Developer Edition bills ~$1.13/hr (~$810/mo) with no on-demand tier, same shape as the OpenSearch/Bedrock-KB calls that kept Tasks 1.4/1.5 at plan-only.

Each step: build → report what/where-to-verify/why → wait for user confirmation → log here before moving on.

## Resources Deployed

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 1 | S3 Bucket | adi-1-1-prompt-templates | arn:aws:s3:::adi-1-1-prompt-templates | Step 2 |
| 2 | DynamoDB Table | adi-1-1-support-conversations | arn:aws:dynamodb:us-east-1:269737522732:table/adi-1-1-support-conversations | Step 3 |
| 3 | IAM Role | adi-1-1-bedrock-lambda-role | arn:aws:iam::269737522732:role/adi-1-1-bedrock-lambda-role | Step 4 |
| 4 | Bedrock Prompt | adi-1-1-support-assistant-persona | arn:aws:bedrock:us-east-1:269737522732:prompt/BIUAWI2H9Z:2 | Step 5 |
| 5 | Bedrock Prompt | adi-1-1-scenario-diagnostic | arn:aws:bedrock:us-east-1:269737522732:prompt/U1O4V7VXQ7:1 | Step 6 |
| 6 | Bedrock Prompt | adi-1-1-scenario-clarification | arn:aws:bedrock:us-east-1:269737522732:prompt/ZXKY89GA4T:1 | Step 6 |
| 7 | Bedrock Prompt | adi-1-1-scenario-escalation | arn:aws:bedrock:us-east-1:269737522732:prompt/IJ65WS1LXQ:1 | Step 6 |
| 8 | S3 Bucket | adi-1-1-cloudtrail-logs | arn:aws:s3:::adi-1-1-cloudtrail-logs | Step 7 |
| 9 | CloudWatch Logs Group | /aws/cloudtrail/adi-1-1-support-assistant | arn:aws:logs:us-east-1:269737522732:log-group:/aws/cloudtrail/adi-1-1-support-assistant:* | Step 7 |
| 10 | IAM Role | adi-1-1-cloudtrail-cwlogs-role | arn:aws:iam::269737522732:role/adi-1-1-cloudtrail-cwlogs-role | Step 7 |
| 11 | CloudTrail Trail | adi-1-1-support-assistant-trail | arn:aws:cloudtrail:us-east-1:269737522732:trail/adi-1-1-support-assistant-trail | Step 7 |
| 12 | IAM Role | adi-1-1-prompt-editor-role | arn:aws:iam::269737522732:role/adi-1-1-prompt-editor-role | Step 8 |
| 13 | Bedrock Guardrail | adi-1-1-support-assistant-guardrail | arn:aws:bedrock:us-east-1:269737522732:guardrail/mti9xf4gepkm (version 2 as of Step 11) | Step 9 |
| 14 | Lambda Function | adi-1-1-detect-intent | arn:aws:lambda:us-east-1:269737522732:function:adi-1-1-detect-intent | Step 10 |
| 15 | Lambda Function | adi-1-1-invoke-model | arn:aws:lambda:us-east-1:269737522732:function:adi-1-1-invoke-model | Step 11 |
| 16 | CloudWatch Logs Group | /aws/vendedlogs/states/adi-1-1-support-assistant-sm | arn:aws:logs:us-east-1:269737522732:log-group:/aws/vendedlogs/states/adi-1-1-support-assistant-sm:* | Step 12 |
| 17 | IAM Role | adi-1-1-stepfunctions-role | arn:aws:iam::269737522732:role/adi-1-1-stepfunctions-role | Step 12 |
| 18 | Step Functions State Machine | adi-1-1-support-assistant-sm | arn:aws:states:us-east-1:269737522732:stateMachine:adi-1-1-support-assistant-sm | Step 12 |
| 19 | Lambda Function | adi-1-1-validate-output | arn:aws:lambda:us-east-1:269737522732:function:adi-1-1-validate-output | Step 13 |
| 20 | CloudWatch Logs Group | /aws/vendedlogs/states/adi-1-1-test-harness-sm | arn:aws:logs:us-east-1:269737522732:log-group:/aws/vendedlogs/states/adi-1-1-test-harness-sm:* | Step 13 |
| 21 | IAM Role | adi-1-1-test-harness-role | arn:aws:iam::269737522732:role/adi-1-1-test-harness-role | Step 13 |
| 22 | Step Functions State Machine | adi-1-1-test-harness-sm | arn:aws:states:us-east-1:269737522732:stateMachine:adi-1-1-test-harness-sm | Step 13 |
| 23 | SNS Topic | adi-1-1-alerts | arn:aws:sns:us-east-1:269737522732:adi-1-1-alerts | Step 14 |
| 24 | CloudWatch Alarm | adi-1-1-invoke-model-errors | (AWS/Lambda Errors, adi-1-1-invoke-model) | Step 14 |
| 25 | CloudWatch Alarm | adi-1-1-support-assistant-sm-failures | (AWS/States ExecutionsFailed) | Step 14 |
| 26 | CloudWatch Alarm | adi-1-1-bedrock-throttles | (AWS/Bedrock InvocationThrottles) | Step 14 |
| 27 | CloudWatch Alarm | adi-1-1-validation-failures | (custom metric, summed across scenarios) | Step 14 |
| 28 | CloudWatch Alarm | adi-1-1-guardrail-interventions | (custom metric, summed across scenarios) | Step 14 |
| 29 | CloudWatch Dashboard | adi-1-1-support-assistant-dashboard | arn:aws:cloudwatch::269737522732:dashboard/adi-1-1-support-assistant-dashboard | Step 14 |

## Step Log

Full detail for all 14 steps (what was built, where to verify, why it matters, every bug hit and its fix) is preserved in full on the website at `Website/src/tasks/task-1-6.html` — written in plain English, step by step, phase by phase. Summary of the 10 real bugs found and fixed along the way:

1. Bedrock model access showed "approved" in console before it was actually usable (propagation delay) — switched to a model that was already working.
2. Newer Bedrock models need a cross-region inference-profile ID, not the bare model ID — `ValidationException` until fixed.
3. Claude Haiku 4.5 rejects requests with both `temperature` and `topP` set — dropped `topP`, republished as prompt v2.
4. Comprehend sentiment alone (96% negative on a normal technical complaint) wrongly triggered human escalation — dropped sentiment as a standalone escalation trigger, kept it as a logged signal only.
5. `bedrock:InvokeModel` doesn't authorize calling a model through a managed Prompt ARN — needed the distinct `bedrock:Converse`/`bedrock:RenderPrompt` actions instead.
6. Cross-region inference profile dispatched to `us-east-2` while IAM only allowed `us-east-1` — wildcarded the region in the resource ARN.
7. Guardrail's `PROMPT_ATTACK` filter at HIGH strength false-positived on a benign, structurally-templated diagnostic query — tuned down to LOW.
8. Step Functions nested-execution (`.sync:2`) creation failed without an EventBridge managed-rule permission — added the specific scoped permission.
9. Assumed `.sync:2` output needed `States.StringToJson` parsing (old `.sync` behavior); actual raw event history showed it's already a parsed object — removed the unnecessary intrinsic.
10. Tried to build a CloudWatch alarm using a dashboard-only `SEARCH()` expression to sum a metric across dimensions — not supported on Alarms; replaced with explicit `MetricStat` entries summed via `FILL(...,0)`.

## Concepts Explained

- Prompt-level instructions (persona) and Guardrails are two independent layers — the persona can in principle be bypassed via prompt injection, while a Guardrail is enforced outside the model regardless of what the prompt says.
- Guardrail filter strength is a confidence threshold, not an on/off switch — HIGH catches more real attacks but also more false positives on legitimate structured input.
- IAM action/resource-type binding is stricter than plain ARN wildcard matching suggests — some actions (like invoking via a managed Prompt) require their own named actions, not coverable by a broader action even with `Resource: "*"`.
- Sentiment/mood detection is a noisy standalone signal for anything consequential (like triggering human escalation) — pair it with a more specific signal (explicit keywords, category) rather than using it alone.
- A flowchart (Step Functions) that runs a second flowchart and waits (`.sync`) needs Step Functions to manage a background EventBridge rule — an easy-to-miss extra IAM permission.

## Next Step

Three genuinely new pieces (not covered by the build above) are planned but not built: JSON Schema (draft-07) response validation, Bedrock Prompt Flows, and a custom-trained Comprehend classifier via async batch jobs. All cheap (no standing hourly cost), just not started yet — see `Website/src/tasks/task-1-6.html` for the detailed plan on each.
