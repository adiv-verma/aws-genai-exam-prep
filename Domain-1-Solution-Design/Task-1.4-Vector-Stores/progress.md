# Task 1.4 — Vector Store Solutions: Build Plan

## Status

**PLANNING ONLY — nothing deployed yet.** This file is a build plan for future sessions, not an executed log. Do not treat any resource below as live; check the AWS Console / `aws` CLI before assuming anything exists. The user flagged cost as a concern (this task is the first one involving a provisioned OpenSearch domain and a Bedrock Knowledge Base, both of which bill by the hour whether idle or not) — see **Cost & Teardown** below before deploying anything.

## Scope decision

`project.md`'s bonus-assignment brief has 6 phases (core infra → processing pipeline → advanced search → external connectors → sync automation → full RAG app with Amplify UI). Following the same pattern as Tasks 1.1–1.3 (real, live, scaled-down PoC rather than the literal enterprise brief), this task will build:

- **Phases 1–3 live** — this is the actual vector-store content the exam tests: store selection/trade-offs, chunking + embedding pipeline, hierarchical/hybrid search.
- **Phases 4–6 architecture-only, not deployed** — web crawler / Confluence / SharePoint connectors, Step Functions sync automation, and an Amplify web app teach integration and frontend skills, not vector-store concepts, and would multiply both cost and build time for no exam payoff. Already captured at the design level in `notes.md` and the Study Notes page (`Website/src/notes/task-1-4.html`) — no further action planned unless requested.

## Planned Resources & Cost

All names follow `adi-1-4-<resource-name>`. **Cost column is the reason each resource needs to be torn down promptly, not left running between sessions.**

| # | Resource | Phase | Est. cost if left running | Notes |
|---|---|---|---|---|
| 1 | IAM role `adi-1-4-bedrock-kb-role` | 1 | Free | Bedrock KB execution role |
| 2 | S3 bucket `adi-1-4-documents-269737522732` | 1/2 | ~$0 (PoC-sized data) | Source docs: `technical-docs/`, `research-papers/`, `policies/` prefixes |
| 3 | Bedrock Knowledge Base `adi-1-4-knowledge-base` (OpenSearch Serverless-backed) | 1 | **~$1/hr (~$700/mo)** — min ~4 OCUs billed even idle | Highest-cost item #1. Delete right after testing each session. |
| 4 | OpenSearch Service domain `adi-1-4-vector-search` | 1/3 | **Scaled down from brief's `r6g.large.search` ×3 (~$360/mo) to `t3.small.search` ×1, single-AZ, 10GB gp3 (~$0.036/hr ≈ ~$26/mo)** | Highest-cost item #2, still real money if left running. Brief's 3-node config is enterprise-scale and unnecessary for a PoC. |
| 5 | DynamoDB table `adi-1-4-document-metadata` | 1 | ~$0 (on-demand billing) | Partition key `document_id`, sort key `chunk_id`, GSI on `document_type` |
| 6 | IAM role + Lambda `adi-1-4-document-processor` | 2 | ~$0 (free-tier covers PoC volume) | S3-triggered: extract text (PDF/DOCX/HTML), chunk, call Titan embeddings, write to OpenSearch + DynamoDB |
| 7 | OpenSearch indices `technical_documentation`, `research_papers`, `company_policies` | 3 | Included in #4 | `knn_vector` mapping (dimension 1536, hnsw/cosinesimil), nested `hierarchy` field for parent-child sections |
| 8 | Lambda `adi-1-4-search-coordinator` | 3 | ~$0 | Manual-invoke only (no API Gateway) — multi-index query fan-out, metadata filters, hybrid (BM25 + kNN) search, result merging. No public endpoint = no idle cost, matches how Task 1.3 handled batch/report-style Lambdas. |

## Planned Step Log (not yet executed)

### Phase 1 — Foundation infra
1. Enable Bedrock model access (Claude + Titan Embeddings) if not already enabled on this account.
2. Create `adi-1-4-documents-269737522732` S3 bucket + prefixes; upload a small synthetic sample set (a few technical docs, a research paper excerpt, a policy doc — same synthetic-data approach as Task 1.3).
3. Create `adi-1-4-bedrock-kb-role`, then the Bedrock Knowledge Base pointed at the S3 bucket, semantic chunking, Titan embedding model.
4. Create `adi-1-4-vector-search` OpenSearch domain (t3.small.search, single node) with the Neural Search plugin enabled, fine-grained access control on.
5. Create `adi-1-4-document-metadata` DynamoDB table (on-demand mode).

### Phase 2 — Document processing pipeline
6. Build `adi-1-4-document-processor` Lambda (S3 `ObjectCreated` trigger): extract text per format, chunk (semantic + overlap), generate Titan embeddings, write chunk metadata to DynamoDB, write vectors to the OpenSearch index.
7. Verify end-to-end: upload one doc per type, confirm chunks land in DynamoDB and vectors land in OpenSearch.

### Phase 3 — Advanced search
8. Create the three OpenSearch indices with hierarchical (nested) mappings and `knn_vector` fields.
9. Build `adi-1-4-search-coordinator` Lambda: query embedding generation, multi-index kNN fan-out, metadata filter clauses, hybrid (keyword + semantic) query, basic re-ranking.
10. Test with a handful of representative queries (one that needs metadata filtering, one that needs hybrid/keyword precision, one pure-semantic) and log actual results.

### Phases 4–6 — Documented, not built
No deployment planned. Covered conceptually in `notes.md` / the published Study Notes page.

## Cost & Teardown — read before deploying anything

The two line items that actually cost money (#3 Bedrock KB, #4 OpenSearch domain) must be torn down at the end of **every session that creates them**, not left running "just in case," and re-created next session if needed (a few minutes of setup, not worth the standing bill). Commands to run before closing out a session:

```bash
# Delete the OpenSearch domain (this is the ~$26/mo item)
aws opensearch delete-domain --domain-name adi-1-4-vector-search --profile awsgenai

# Delete the Bedrock Knowledge Base (this is the ~$700/mo item — the one to never leave running overnight)
aws bedrock-agent delete-knowledge-base --knowledge-base-id <KB_ID> --profile awsgenai

# Everything else (DynamoDB, Lambda, S3, IAM) is effectively free to leave running, but clean up at task end regardless
```

Before starting a build session on this task, confirm out loud (in chat) that the OpenSearch domain and Bedrock KB are either about to be created fresh or were already destroyed at the end of the last session — don't assume either is still down.

## Concepts Explained

_(To be filled in as Phases 1–3 are actually built.)_

## Next Step

Awaiting go-ahead to start Phase 1 (Step 1 above). Nothing deployed yet.
