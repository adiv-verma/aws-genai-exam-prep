Domain 1, Task 1.5: Design Retrieval Mechanisms for FM Augmentation — Comprehensive Study Notes
Scenario Overview
Target Enterprise: A global law firm operating across 25 countries handling case law, legal opinions, contracts, and regulatory filings.
Core Requirements: Accurate context-aware answers, multi-jurisdictional research, strict client confidentiality, mandatory citations to source documents on every response, and sub-second response times.
Outcomes Achieved: Research time reduced by 70%, 42% more relevant precedents discovered, 92% retrieval recall, and 95% of attorneys reporting higher confidence in AI-assisted output.
Task 1.4 vs. Task 1.5 Focus Comparison
Task 1.4 Focus: Infrastructure, storage tiering, sharding, caching, synchronization, and where the vector store lives and is maintained.
Task 1.5 Focus: Retrieval quality—document segmentation, embedding generation, query handling, and reranking to optimize recall and relevance.
1. Document Segmentation (Chunking)
Legal chunking presents a unique engineering challenge. For example, consider the clause:
"The Party may terminate this Agreement, provided that Section 5.1 conditions are met."

If a naive chunking boundary splits this sentence right before the proviso, the chunk reads "Party may terminate", while the critical conditions vanish, inverting the legal meaning. Poor chunking leads directly to flawed legal reasoning.
Four Core Chunking Strategies
Fixed-Size Chunking:
Cuts text every N words.
Simple and fast, but entirely blind to structural hierarchy (clauses break mid-sentence). Suitable only for plain narrative text.
Structure-Aware Chunking:
Cuts on natural document boundaries like headings (<h1>, <h2>, <p>) and paragraph breaks rather than word counts.
Unstructured text is first converted into a structured format (e.g., HTML/Markdown) to expose logical divisions, ensuring each chunk represents a complete logical unit.
Hierarchical (Parent-Child) Chunking:
Leverages a two-tier architecture.
The system searches small child chunks to achieve high retrieval precision, but passes the corresponding large parent chunk to the Foundation Model (FM) to preserve comprehensive surrounding context. This is natively supported within Bedrock Knowledge Bases.
Example Structure:
PARENT: Article 5 - Termination (2000 words)
-- CHILD: 5.1 Conditions (300 words)
-- CHILD: 5.2 Notice period (250 words)
-- CHILD: 5.3 Effects (400 words)
Semantic Chunking:
Automatically detects topic shifts by calculating similarity scores between consecutive sentences.
Computationally expensive during ingestion because embeddings must be calculated on-the-fly, but yields highly natural and logically bounded chunks.
Bedrock Knowledge Bases Chunking Options
Default / Fixed-Size: ~300 tokens with configurable overlap.
Hierarchical: Parent-child configuration.
Semantic: Meaning-based boundary detection.
No Chunking: Treats one entire file as one chunk (ideal for small memos/documents).
Lambda Custom Chunking: Invokes a custom Lambda function when documents land in the S3 data source, executing specialized code for complex document types.
Exam-Relevant Rule: Chunking strategy must be selected per document type, not applied uniformly across an entire enterprise corpus. For instance, internal opinions might use structure-aware Lambda parsing, whereas case law leverages hierarchical parent-child structures.

Metadata Integration & Boundary Overlap
Metadata Attachment: Metadata elements (such as jurisdiction, practice area, precedential value, and date) must be attached during the chunking phase. Attempting to add or modify metadata after vectors are stored requires a costly and slow full-corpus re-ingestion.
Boundary Overlap (~10%): A small overlap between consecutive chunks ensures that statements spanning split boundaries are fully preserved in both chunks, protecting semantic meaning from being cut off.
2. Embedding Solutions
Embeddings transform textual chunks into high-dimensional numerical representations (vectors) that capture semantic meaning.
Dimensionality
Amazon Titan Text Embeddings: Operates natively at 1,536 dimensions (a key value to memorize for the exam). Titan V2 also offers selectable options of 1024, 512, or 256 dimensions.
Trade-offs:
High Dimensions (e.g., 1,536): Captures finer nuances, deeper context, and higher similarity fidelity, but demands more storage, higher RAM, and slower search latency.
Low Dimensions (e.g., 256/512): Faster and cheaper, but risks losing subtle legal distinctions.
Analogy (The "Meters" Concept): Think of dimensionality as a panel of 1,536 independent analytical meters (scoring various legal topics, tones, and subject matters). A higher dimension count provides a higher-resolution profile of the text, while a lower dimension count compresses the profile into broad, generalized scores.
Dense vs. Sparse Embeddings
Dense Embeddings (Semantic): Every dimension holds a floating-point value. They map the underlying semantic meaning and concept relationships (e.g., matching "employee relocation" with "restrictive covenant").
Sparse Embeddings (Keyword): Composed mostly of zero values with non-zero weights assigned to exact terms (mirroring traditional keyword systems like BM25). They excel at exact string matching, statute numbers, and proper nouns.
Hybrid Need: Legal workflows require both exact citations (Sparse) and conceptual reasoning (Dense), driving the need for Hybrid Search architectures.
Binary Embeddings & Quantization (Cost Optimization)
Standard float32 representations consume 4 bytes per dimension.
Binary Embeddings compress each dimension down to a single bit (0 or 1), yielding ~32x reduction in storage space.
Titan and OpenSearch Serverless support binary vectors and FP16 quantization to drastically cut infrastructure costs without significant drops in accuracy.
Domain Fit & Model Consistency
General vs. Legal Vocabulary: General embedding models trained on web corpora misinterpret legal terminology (e.g., interpreting "consideration" as cognitive reflection rather than exchange of value, or "party" as a celebration rather than a legal entity). Specialized domains require fine-tuned or domain-adapted embedding models.
The Golden Rule of Consistency: The exact same embedding model must be used for both document ingestion and runtime query generation. Switching embedding models shifts the vector space entirely, breaking similarity matching and necessitating a complete corpus rebuild.
3. Vector Search Deployment
Selecting the right storage backend and architecture governs scalability, cost, and multi-tenant isolation.
Vector Store Options
Bedrock Knowledge Bases (Fully Managed):
Manages end-to-end ingestion, chunking, embedding generation, and storage natively. Ideal for standard RAG setups requiring minimal custom overhead.
OpenSearch Serverless:
High-performance vector engine supporting binary vectors, FP16 quantization, hybrid search, and fine-grained access control. Best for highly sensitive enterprise data.
Aurora PostgreSQL + pgvector:
Combines relational data management with vector similarity search in a single query engine. Ideal when structured metadata filters and relationships carry equal weight to similarity scores.
Example Single-Query Pattern:
SQL
SELECT * FROM cases 
WHERE jurisdiction = '9th Circuit' 
  AND date > '2020-01-01' 
ORDER BY embedding <-> query_embedding 
LIMIT 10;
Multi-Tenant Architectures (SaaS Patterns)
Silo Model: Separate index or database per tenant. Maximum security and isolation, but highest cost.
Pool Model: Shared database/index store across tenants, filtered dynamically via a tenant_id parameter. Most cost-effective, but entirely dependent on correct application filtering; a single query bug risks catastrophic cross-tenant data leaks.
Bridge Model: Shared infrastructure with separate database schemas (middle ground).
Enterprise Practice: Law firms frequently mix patterns—deploying Silo models for high-stakes or enterprise clients, and Pool models for smaller matters. In pool architectures, tenant filters must be enforced strictly within the database query execution layer, never left solely to client application logic.
Security Controls & PII Redaction
Encryption & Access Control: Data encrypted at rest via KMS and in transit via TLS, paired with IAM roles and fine-grained document/field-level permissions in OpenSearch.
PII Redaction: Personal Identifiable Information must be scrubbed or masked prior to embedding generation. Once PII is embedded into vector coordinates, it becomes mathematically opaque and nearly impossible to cleanly delete or extract.
4. Advanced Search Architectures
To bridge the gap between abstract conceptual queries and rigid legal requirements, advanced search pipelines combine multiple retrieval layers.
Hybrid Search (Vector + BM25)
Combines Dense Vector Search (capturing broad conceptual intent) with Sparse BM25 Search (capturing exact citation strings, statute codes, and proper nouns).
Configured in Bedrock Knowledge Bases via OverrideSearchType = HYBRID.
Constraint: Requires underlying vector stores (such as OpenSearch Serverless with filterable text fields) that natively support hybrid scoring.
Two-Stage Retrieval with Rerankers
Stage 1 (Coarse & Fast): Hybrid search scans millions of chunks to retrieve the top 100 candidate documents.
Stage 2 (Precise & Slow): A specialized Reranker model (e.g., Cohere Rerank or Amazon Rerank) jointly analyzes the user query alongside each candidate chunk, applying deep contextual cross-attention scoring to re-order and distill the list down to the definitive top 10.
Why two stages? Running deep cross-attention models across an entire corpus of 15 million documents is computationally prohibitive. Two-stage retrieval balances lightning speed with supreme accuracy.
Legal-Specific Relevance Boosts
Citation Network Analysis: Boosts document ranking based on graph-based authority (how frequently a precedent is cited by higher courts), independent of semantic similarity.
Jurisdiction-Aware Filtering: Applies context filters matching the attorney's practicing jurisdiction.
Precedential Value Boosts: Elevates landmark rulings over lower court decisions.
5. Query Handling Systems
Attorneys rarely type queries in optimal formats for vector databases. Query handling systems preprocess and enrich user input before search execution.
Query Expansion (via Bedrock):
Automatically expands brief user queries (e.g., expanding "non-compete enforceability" to include restrictive covenants, employee mobility restrictions, trade secret protection) to capture alternative legal terminology used across different documents. Yields up to a 23% boost in recall.
Query Decomposition (via Lambda & Step Functions):
Breaks complex multi-part questions (e.g., "Can a non-compete be enforced in California if the employee relocated to Texas, and trade secrets are involved?") into independent sub-queries.
Utilizes AWS Step Functions to execute parallel sub-query searches, merging results before passing them to the reranker, reducing overall response latency by up to 40%.
Graph-Enhanced Retrieval & Event-Driven Indexing:
Neptune Analytics: Combines graph traversals with vector search (.vectors.topKByEmbedding), enabling queries like "find documents semantically similar to this case AND explicitly cited by the Supreme Court".
Event-Driven Indexing: S3 document uploads trigger EventBridge Pipes, feeding updates directly into embedding pipelines and vector stores without manual glue code.
6. Integration with Foundation Models
The final retrieval output must be securely and auditably wired into the Foundation Model.
RAG with Mandatory Citations: Chunks are passed to the FM alongside rich metadata mapping [Chunk N -> Source Citation]. The model embeds exact source citations in its output, allowing attorneys to verify every claim.
Function Calling & Bedrock Agents: Shifts control to the model, allowing it to dynamically invoke specific retrieval or validation tools (e.g., search_cases() and check_overturned()) based on complex multi-step reasoning needs.
Model Context Protocol (MCP): Acts as a standardized protocol (analogous to a USB cable) between AI models and diverse enterprise data sources, eliminating custom connector code for every tool integration.
Comprehensive Audit Logging: Non-negotiable in legal engineering. Every interaction—capturing incoming queries, retrieved source documents, assembled system prompts, and model responses—must be immutably logged to ensure verifiable audit trails months or years later.