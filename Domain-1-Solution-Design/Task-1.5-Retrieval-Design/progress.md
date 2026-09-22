# Task 1.5 — Retrieval Mechanisms for FM Augmentation — Progress

## Status

**Live build complete for this task, by deliberate choice.** Steps 1–3 (S3 + sample data + IAM role, the chunking engine, the embedding generator) are deployed and verified. The retrieval-evaluator (originally planned Step 4) and all of Phases 3–6 are being left as **plan-only, not deployed** — see **Scope decision** below. Nothing further is planned unless requested.

## Scope decision

`project.md`'s brief has 6 phases (chunking → embeddings → 3-way vector store deployment → hybrid/rerank search → query decomposition → API integration layer). Following the same reasoning as Task 1.4, but split more finely this time:

- **Phases 1–2 LIVE (Steps 1–3)** — document chunking (3 strategies) + embedding generation (Titan vs. Cohere), over a real synthetic corpus, with zero provisioned infrastructure — S3 + Lambda + on-demand Bedrock calls only.
- **The retrieval/evaluation step (originally planned Step 4/5) and Phases 3–6 documented only, not deployed** — by deliberate choice, once Steps 1–3 had already produced enough real, verifiable output (chunk divergence across strategies, embeddings from two different models) to make the case either way. The retrieval-evaluator would have done brute-force cosine-similarity search over the Step 3 embeddings to score all 6 (strategy × model) combinations against the 12-query ground-truth set — a real, useful, near-zero-cost technique (see the "is it useful at all" discussion earlier in this task), just not carried through to an actual deployment this round. Phase 3 separately asks for **three parallel provisioned/managed vector stores at once** (OpenSearch Service domain — the brief's own config is 2 data + 3 dedicated-master `r6g.large.search` nodes, Aurora PostgreSQL + pgvector, and a Bedrock Knowledge Base backed by OpenSearch Serverless) purely to benchmark them against each other. The Bedrock KB alone bills ~$1/hr (~$700/mo) even idle — the identical line item that kept Task 1.4 at notes-only — and this brief adds a second always-billing OpenSearch domain and a third provisioned Aurora instance on top of that. Phases 4–6 (hybrid search tuning, query decomposition via Step Functions, API Gateway integration layer) all sit on top of whichever store from Phase 3 gets picked, so they inherit the same "not worth the standing bill for a PoC" call. Already captured at the design level in `notes.md` and the Study Notes page (`Website/src/notes/task-1-5.html`) — no further action planned unless requested.

## Pre-flight check

- AWS identity confirmed: account `269737522732`, profile `awsgenai`.
- Bedrock embedding model access confirmed **already enabled**, no request needed: `amazon.titan-embed-text-v1` (1536-dim) and `cohere.embed-english-v3` (1024-dim) both invoked successfully with test text.
- No resource named `adi-1-5-*` exists yet on this account.
- Estimated total cost for the live scope: **well under $1** — no provisioned/hourly resource at all, just S3 + Lambda + on-demand Bedrock embedding calls (a few hundred short-text invocations for a handful of synthetic documents and ~10-12 test queries).

## Scenario (scoped for a solo PoC)

`project.md`'s own example is AWS technical documentation (not the law-firm scenario used in `notes.md`'s exam-style study notes — that stays as-is on the Study Notes page). Sample data: 6 synthetic technical articles about AWS services (S3 storage classes, Lambda concurrency, DynamoDB capacity modes, Bedrock Knowledge Bases, OpenSearch vector search, Step Functions), each with multiple `##` sections, so fixed-size chunking will sometimes split mid-section while hierarchical/semantic chunking should recover section boundaries — giving the 3 strategies genuinely different behavior to measure, not just cosmetic differences.

Naming: `adi-1-5-` prefix. Region: `us-east-1` (Bedrock access already confirmed there in Tasks 1.2/1.3).

## Phased Build Plan

### Phase 1 — Document processing & segmentation (LIVE)
1. S3 bucket `adi-1-5-documents-269737522732` (`raw-docs/`, `chunks/`, `embeddings/`, `evaluation/` prefixes) + author and upload 6 synthetic technical docs + a hand-authored test-query set with ground-truth answer sections.
2. IAM role `adi-1-5-lambda-role` (S3 read/write on the bucket, Bedrock `InvokeModel`, CloudWatch Logs).
3. Lambda `adi-1-5-chunking-engine`, S3-triggered on `raw-docs/` uploads: implements **fixed-size** (with overlap), **hierarchical** (split on `##`/`###` headings, parent+child), and **semantic** (embed consecutive sentences, split where cosine similarity drops below a threshold — the real technique behind "semantic chunking," not an LLM-generation call) strategies. Writes chunks + metadata to `chunks/{strategy}/{doc_id}/`.

### Phase 2 — Embedding generation & optimization (LIVE)
4. Lambda `adi-1-5-embedding-generator`, manually invoked (batch job, no public endpoint — same "no idle cost" pattern as Task 1.4's `search-coordinator`): for every chunk across all 3 strategies, generates embeddings with **both** `titan-embed-text-v1` and `cohere.embed-english-v3`, batched, written to `embeddings/{model}/{strategy}/{doc_id}/`.

### Retrieval evaluation — designed, not deployed
A `adi-1-5-retrieval-evaluator` Lambda was scoped (manually invoked: for each of the 6 strategy × embedding-model combinations, embed each test query, brute-force cosine-similarity search over that combination's stored chunk embeddings, check the top result(s) against the `test_queries.json` ground truth, compute Hit-Rate@3 / MRR per combination, plus a pure embedding-quality check on known-similar vs. known-dissimilar chunk pairs) but, by choice, not built this round — Steps 1–3 already demonstrate the useful, zero-infrastructure part of this task (real chunking divergence, real embeddings from two models); scoring which combination retrieves best is documented as the next concrete step if this task is picked back up.

### Phases 3–6 — Documented, not built
No deployment planned (see Scope decision above). Vector-store trade-offs, hybrid/rerank search, query decomposition, and the API integration layer are already covered conceptually in `notes.md` and the Study Notes page.

## Resources Deployed

| # | Resource Type | Name | Identifier (ARN/ID) | Step |
|---|---|---|---|---|
| 1 | S3 Bucket | adi-1-5-documents-269737522732 | arn:aws:s3:::adi-1-5-documents-269737522732 | Step 1 |
| 2 | IAM Role | adi-1-5-lambda-role | arn:aws:iam::269737522732:role/adi-1-5-lambda-role | Step 1 |
| 3 | Lambda | adi-1-5-chunking-engine | arn:aws:lambda:us-east-1:269737522732:function:adi-1-5-chunking-engine | Step 2 |
| 4 | Lambda | adi-1-5-embedding-generator | arn:aws:lambda:us-east-1:269737522732:function:adi-1-5-embedding-generator | Step 3 |

## Step Log

### Step 1 — S3 bucket + synthetic sample dataset + IAM role
- **What:** Created `adi-1-5-documents-269737522732` (`us-east-1`, versioning on, all public access blocked). Authored 6 synthetic technical-documentation articles (`data/raw-docs/*.md`) covering S3 storage classes, Lambda concurrency, DynamoDB capacity modes, Bedrock Knowledge Bases, OpenSearch vector search, and Step Functions workflows — each with 4-5 `##` sections of substantial, distinct content, so fixed-size chunking will sometimes cut mid-section while hierarchical/semantic chunking should recover section boundaries cleanly. Hand-authored a 12-query test set (`data/test_queries.json`) with each query mapped to a specific `doc_id` + `expected_section` ground truth, to be used for retrieval evaluation in a later step. Uploaded all 6 docs to `raw-docs/` and the query set to `test-queries/`. Created `adi-1-5-lambda-role` (trusts `lambda.amazonaws.com`; scoped to S3 read/write on the bucket, `bedrock:InvokeModel` on Titan Embed and Cohere Embed only, and CloudWatch Logs).
- **Where to check:** Console → **S3 → adi-1-5-documents-269737522732** — `raw-docs/` (6 objects) and `test-queries/` (1 object). **IAM → Roles → adi-1-5-lambda-role** — inline policy `adi-1-5-lambda-permissions`.
- **Why:** `project.md`'s own example scenario is AWS technical documentation (distinct from `notes.md`'s law-firm exam scenario, which stays as-is on the Study Notes page), so the sample data matches that. Pre-flight also confirmed Bedrock embedding access already works: `amazon.titan-embed-text-v1` (1536-dim) and `cohere.embed-english-v3` (1024-dim) both invoked successfully with test text before building anything — no model-access request needed, unlike Task 1.4's initial assumption.
- **Verified:** `aws s3 ls --recursive` confirms all 7 objects; `aws iam get-role` confirms the role ARN.

### Step 2 — Chunking engine Lambda (fixed-size, hierarchical, semantic), S3-triggered
- **What:** Built `lambda/chunking-engine/lambda_function.py` and deployed it as `adi-1-5-chunking-engine` (Python 3.13, 256MB, 90s timeout, `adi-1-5-lambda-role`). Implements all 3 strategies from `notes.md`/`project.md` over the same source document:
  - **Fixed-size** — 800-char chunks with 100-char overlap, snapping to the nearest sentence boundary within the chunk window (adapted from `project.md`'s own sample function).
  - **Hierarchical** — splits on `## ` headings; each section becomes one chunk tagged with its `section_title`, plus an intro chunk for any text before the first heading. Since these docs only use one heading level, "hierarchical" here reduces to one chunk per section — still genuinely structure-aware, just without a deeper parent/child nesting these particular docs don't have.
  - **Semantic** — the technique `notes.md` actually describes ("detects topic shifts by calculating similarity scores between consecutive sentences"), not an LLM-generation call: splits the doc into sentences, embeds each with Titan, and cuts wherever consecutive-sentence cosine similarity drops below that *document's own* `mean - 0.5×stdev` (a per-document statistical threshold rather than one guessed constant, since raw similarity scores aren't comparable across different content) — with a 2-sentence minimum and 1,200-char maximum as guardrails against degenerate 1-sentence or single-mega-chunk output.
  - Wrote an S3 event notification (`s3:ObjectCreated:*` on `raw-docs/` with `.md` suffix) plus the matching Lambda resource policy, then re-uploaded all 6 sample docs to fire the trigger live rather than only testing via manual invoke.
- **Where to check:** Console → **Lambda → adi-1-5-chunking-engine** (Configuration → Trigger shows the S3 event source) → **Monitor → Logs** (6 invocations, zero errors). **S3 → adi-1-5-documents-269737522732 → chunks/{fixed,hierarchical,semantic}/** — 33 fixed + 36 hierarchical + 30 semantic chunk objects across the 6 docs.
- **Why:** This is the actual exam-tested content of Phase 1 — comparing how the same source text fragments differently under each strategy. Concretely verified on `s3-storage-classes.md` before deploying: fixed-size cut mid-sentence/mid-section as expected (e.g., one chunk starts mid-word on "ency and high throughput..."); hierarchical recovered all 6 sections cleanly; semantic produced 5 chunks that mostly tracked section boundaries but **merged** the "Standard-IA/One Zone-IA" and "Glacier storage classes" sections into a single chunk — a genuine, real example of semantic chunking finding two adjacent headings similar enough in meaning (both about lower-cost/infrequent-access tiers) to not warrant a split, which a purely structural strategy would never do. That divergence between strategies is exactly what Phase 1 Step 3's evaluation (next steps) needs to measure.
- **Verified:** Re-uploaded all 6 source docs; `aws s3 ls --recursive` on `chunks/` shows the expected 3-strategy × 6-doc output; `aws logs filter-log-events --filter-pattern ERROR` on the function's log group returned nothing.

### Step 3 — Embedding generator Lambda (Titan + Cohere), manually invoked
- **What:** Built `lambda/embedding-generator/lambda_function.py`, deployed as `adi-1-5-embedding-generator` (Python 3.13, 256MB, 300s timeout, `adi-1-5-lambda-role`, `DOCUMENTS_BUCKET` env var). No event trigger — manual-invoke batch job, same "no public endpoint = no idle cost" pattern as Task 1.4's `search-coordinator`. Lists every chunk under `chunks/`, then embeds each one with **both** `amazon.titan-embed-text-v1` (one call per chunk — Titan v1 has no native multi-text batch input) and `cohere.embed-english-v3` (batched 20 texts per call, matching `project.md`'s own `batch_generate_embeddings` sample and its stated Phase 2 Step 2 goal of "batch processing for efficiency"). Writes each result to `embeddings/{titan|cohere}/{strategy}/{doc_id}/chunk_NNN.json`, carrying forward the chunk's own metadata plus `model`, `embedding`, and `embedding_dim`.
- **Where to check:** Console → **Lambda → adi-1-5-embedding-generator** → **Monitor → Logs** (one invocation, `{"titan": 99, "cohere": 99, "total_chunks": 99}`). **S3 → adi-1-5-documents-269737522732 → embeddings/** — `titan/` and `cohere/`, each with all 3 strategies × 6 docs = 99 objects apiece, 198 total.
- **Why:** Generates the two embedding sets the retrieval evaluator (next step) needs to score Titan vs. Cohere head-to-head on identical chunk sets, and demonstrates the batch-vs-single-call distinction between the two models directly (a real, observable API difference, not just a line in the notes).
- **Verified:** Single invocation returned `{"titan": 99, "cohere": 99, "total_chunks": 99}` in ~27s; `aws s3 ls --recursive` on `embeddings/` shows 6 (model × strategy) folders × 6 docs each; spot-checked one object — correct metadata carried through, 1536-dim Titan vector present; `aws logs filter-log-events --filter-pattern ERROR` returned nothing.

## Concepts Explained

- **Chunking strategy choice is genuinely content-dependent, not academic.** On the real corpus here, fixed-size chunking visibly cut mid-sentence/mid-word; hierarchical cleanly recovered every `##` section; semantic chunking (built on real consecutive-sentence embedding similarity, not an LLM call) matched section boundaries most of the time but *merged* two adjacent sections whose content was semantically close enough — a real, observable difference between "structure-aware" and "meaning-aware" chunking that a written description alone doesn't make concrete.
- **A per-document statistical threshold beats one global constant for semantic chunking.** Embedding similarity scores aren't comparable in absolute terms across different documents/content, so the boundary threshold (`mean − 0.5×stdev` of that document's own consecutive-sentence similarities) is computed fresh per document rather than picked as one fixed number for every doc.
- **Titan vs. Cohere embedding API shape is a real, load-bearing difference, not a trivia fact.** Titan Embed v1 only accepts one input text per `invoke_model` call; Cohere Embed accepts a batch of texts in one call. That difference is exactly why `project.md`'s own sample code batches Cohere calls but loops Titan calls one at a time — confirmed directly by building both paths, not just read about it.
- **A vector store doesn't have to be a managed service to prove out retrieval quality.** For a PoC-sized corpus, brute-force cosine-similarity search over embeddings held flat in S3/memory is the same *exact* search a managed index does (OpenSearch/pgvector only earn their cost once approximate search is needed at scale) — this is why Phases 1–2 could be built for real with zero provisioned infrastructure, while Phase 3's three-way managed-store comparison could not be justified the same way.

## Next Step

None planned. If this task is picked back up: build `adi-1-5-retrieval-evaluator` per the "Retrieval evaluation — designed, not deployed" section above to get real Hit-Rate@3/MRR numbers across all 6 (strategy × model) combinations.
