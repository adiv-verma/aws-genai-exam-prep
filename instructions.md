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
- `Website/src/tasks/task-<domain>-<task>.html` — one deep-dive page per task (e.g. `task-1-1.html`). **Structure it as a chronological step log, mirroring `progress.md`'s Step Log directly — do not split "what we built" / "errors" / "exam tips" into separate flat sections.** Concretely (see `task-1-1.html` as the reference example):
  - Group steps under phase dividers (Phase 1, Phase 2, ...), same phase names as `progress.md`.
  - One card per step, in order, each with: the resource name(s) it created, **What** (what got built, with actual resource names, not categories), **Where** (exact console path), **Why** (the concept it teaches).
  - Any error/bug hit *during that step* goes inline in that same step's card, immediately after the What/Where/Why — symptom, root cause, and the actual fix. Number bugs sequentially across the whole page (Bug 1, Bug 2, ...) so the hero stat count stays accurate.
  - An exam tip goes inline in that same step's card too — one per step, tied to what that step actually taught (not just the steps that had bugs).
  - Keep a compact resource-index table (name + type + one-line purpose) at the end as a quick-reference appendix, but it is *not* where the explanation lives — the step cards are the primary content.

**Update the task's page progressively, phase by phase, as work happens** — the same way `progress.md` is appended to after every confirmed step, not written once at the end. When a step's resource(s) are deployed (and after any bug is found/fixed during that step), add that step's card to the task's page in the same pass as the `progress.md` update, so the site and the progress log never drift out of sync.

- **"Study Notes"** — the user's own condensed exam cheat-sheets, kept **separate from the Build Log** (Build Log = what was actually deployed; Notes = personal study material, often describing a broader reference architecture than any one PoC builds). Follows the exact same hub + one-page-per-task pattern as the Build Log, for the same reason (don't cram every task onto one page — dozens of tasks across 5 domains need real navigation):
  - `Website/src/notes/index.html` — the hub: a `.domain-head` divider per domain (`Domain 1`, `Domain 2`, ...) that actually has notes, each followed by a `.task-card` linking out per task, in task-number order. Only list domains/tasks that exist — don't pre-create empty ones.
  - `Website/src/notes/task-<domain>-<task>.html` — one full page per task (e.g. `task-1-1.html`), with its own nav (`All Study Notes` back to the hub, plus a link to that task's Build Log page).
  - **When a task folder contains a `notes.md` and/or an `architecture_diagram.jpg`** (or similarly named image), that's the signal to create/update that task's notes page:
    - Copy the image to `Website/src/assets/task-<domain>-<task>-architecture.<ext>` (flat, mirroring the page naming) and embed it via `<figure class="arch">` with a real, descriptive `alt` text (not just a filename) and a one-sentence `<figcaption>`.
    - Render the notes content as a grid of `.note-card` blocks (one per top-level heading in the source `notes.md`, using `<dl>`/`<dt>`/`<dd>` for term:description pairs) — reflow/tighten the prose for a card format, don't just dump raw markdown into a `<pre>`.
    - Add (or update) that task's `.task-card` on the hub page — create a new `.domain-head` divider too if it's the first task for that domain.
  - Cross-link both directions: the task's Build Log page (`tasks/task-<domain>-<task>.html`) links to `../notes/task-<domain>-<task>.html`, and the notes page links back to `../tasks/task-<domain>-<task>.html`.
  - `notes.md` / `architecture_diagram.jpg` themselves stay in the task folder (source material, like `project.md`) — they are not deleted after being folded into the site.

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
