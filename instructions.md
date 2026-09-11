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
