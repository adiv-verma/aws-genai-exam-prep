# Project Instructions

## AWS Profile

Always use the `awsgenai` AWS CLI profile for this project — do not use the `default` profile.

- Account ID: 269737522732
- IAM User: admin

When running AWS CLI commands, pass `--profile awsgenai`, e.g.:

```bash
aws sts get-caller-identity --profile awsgenai
```

Or export it for the session:

```bash
export AWS_PROFILE=awsgenai
```

## Resource Naming Convention

This AWS account is shared with others. Every resource created (S3 buckets, IAM roles, EC2 instances, Lambda functions, security groups, etc.) must be prefixed with `adi-` so ownership is clear and naming doesn't collide with other users' resources.

In addition, every resource must include the **domain-task number** it belongs to, right after the `adi-` prefix, so resources from different tasks don't collide and ownership-by-task is clear at a glance. Format: `adi-<domain>-<task>-<resource-name>` (dash-separated, no dots — dots are avoided for S3 bucket-name safety/consistency across resource types).

Example: for Task 1.1 (Domain 1, Task 1) → `adi-1-1-prompt-templates`, `adi-1-1-lambda-role`, `adi-1-1-support-conversations`. For Task 2.3 → `adi-2-3-integration-queue`.

## GitHub

This project is version-controlled at **https://github.com/adiv-verma/aws-genai-exam-prep** (public), remote `origin`.

- Commit and push at the end of every task (or every session that makes meaningful progress on a task) — don't let work sit uncommitted across sessions.
- Before committing: run a quick scan for anything that looks like a real credential (access keys, secrets, tokens) — none of this project's own content should ever contain one, but double-check before `git add -A` regardless.
- Use a real commit message describing what was built/changed, ending with the standard `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` trailer.

## Companion Website

A static study-guide site lives at `Website/src/` and is deployed to:

- **S3 bucket:** `adi-genai-exam-site-269737522732`
- **CloudFront distribution:** `E3883M6668QGYO` → **https://dwllzc5nxt67o.cloudfront.net**

Structure:
- `Website/src/index.html` — the main AIP-C01 exam-overview landing page.
- `Website/src/tasks/index.html` — the "Build Log" hub, one card per completed task.
- `Website/src/tasks/task-<domain>-<task>.html` — one deep-dive page per task (e.g. `task-1-1.html`), covering: what was built (by phase, **with actual resource names and a one-two line description of what each one does/why it's there** — mirror `progress.md`'s level of detail, not a vague summary), real errors hit and how they were actually fixed (root cause, not guesses), how to verify each piece in the console, and exam-relevant takeaways tied to the concepts the task exercised.

**Update the task's page progressively, phase by phase, as work happens** — the same way `progress.md` is appended to after every confirmed step, not written once at the end. When a phase/step's resources are deployed, add them (names, not just categories) to that task's page in the same pass as the `progress.md` update, so the site and the progress log never drift out of sync.

Deploy after any change:
```bash
aws s3 sync Website/src/ s3://adi-genai-exam-site-269737522732/ --profile awsgenai --delete
aws cloudfront create-invalidation --distribution-id E3883M6668QGYO --paths "/*" --profile awsgenai
```
(Scope the sync/invalidation to just the changed file(s) for a quick mid-task update; do a full `/*` sync+invalidation as the final step of a task.)

## Task Workflow & Resumability

Each `Domain-*/Task-*/` folder is a self-contained project with three files:

- **`project.md`** — the requirements/brief, pasted in by the user. Source of truth for what to build. Not edited by Claude.
- **`progress.md`** — the resumable deployment log. This is the file to read first when picking up a task in a new chat. Structure:
  - **Status** line at the top: current step, what's done, what's next.
  - **Resources Deployed** table: resource type, name (with `adi-` prefix), key identifiers (ARN/ID), step it belongs to.
  - **Step Log**: one entry per deployment step, in order — what was created/configured (command or console action), why (the concept it teaches), and confirmation that the user verified it in the AWS console.
  - **Concepts Explained**: running list of concepts covered so far, so they aren't re-explained from scratch on resume.
- **`instructions.md`** — task-specific deviations from this root file, if any (usually stays empty; the root conventions apply by default).

### Working process for every task

1. Read `project.md` (requirements) and `progress.md` (current state) before doing anything.
2. Work **one resource/step at a time** — do not batch-deploy. After creating/configuring a resource, always report back:
   - **What** was created (resource name/type, with `adi-` prefix).
   - **Where to check it** — exact AWS console path (service, region, page) so the user can go verify it.
   - **Why** it was created — the concept it teaches, tied to the exam domain/task.
   - Wait for the user to confirm before moving to the next step.
3. If the user asks follow-up questions about a step, answer them, then append the Q&A (or the key takeaway from it) to that step's entry in `progress.md` / Concepts Explained — don't let explanations live only in chat.
4. After each confirmed step, append to `progress.md` immediately (status, resource table, step log, concepts) — don't wait until the end of the session. This is what makes the task resumable if the chat is lost.
5. All resources use the `awsgenai` profile and the `adi-` naming prefix (see above).

### Sample data

When a task needs data to work with (documents, records, test queries, etc.), Claude generates realistic sample data matching the project's use case and puts it in a `data/` subfolder inside that task folder (e.g. `Task-1.1-Architecture-and-PoC/data/`). Log what was generated and why in `progress.md` like any other step.
