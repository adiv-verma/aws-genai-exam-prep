Comprehensive Architectural Summary & Exam Cheat Sheet: Task 1.1
This master summary and cheat sheet consolidates all components, architectural patterns, and exam tips discussed for Task 1.1, designed for the AWS Certified Generative AI Developer — Professional exam.
1. Entry, Networking & Authentication Layer
AWS Global Accelerator: Provides 2 Static Anycast IPs and utilizes the AWS private backbone network. Use this for global users requiring low-latency WebSocket/TCP streaming and static IP whitelisting (bypassing public internet jitter).
AppSync & WebSockets: Powers real-time token streaming via GraphQL subscriptions. To overcome AppSync's 30-second integration timeout limit for heavy LLM responses, implement an Async Mutation pattern that immediately returns a conversationId, followed by persistent WebSocket subscriptions to stream tokens.
Amazon Cognito & JWT: Handles stateless token verification at the AppSync layer. For immediate session revocation requirements, combine short-lived JWT TTLs with a revocation check against a fast key-value store (e.g., Redis or DynamoDB).
2. Core RAG & Knowledge Base Pipeline
Bedrock Knowledge Base (KB): Fully managed, serverless RAG orchestration that manages document ingestion, chunking, and vector embedding generation.
Multilingual Embeddings: Eliminates the need for explicit translation steps. Queries map directly within a cross-lingual vector space, allowing a query in one language to match relevant document chunks in another.
3. Vector Stores & Storage Decision Matrix
OpenSearch Serverless: The default, ultra-low latency vector engine. CRITICAL EXAM RULE: OpenSearch Serverless is mandatory when integrating SaaS data sources such as SharePoint, Salesforce, or Confluence into Bedrock KBs.
Amazon S3 Vectors: A cost-optimized storage choice for massive-scale datasets where sub-second latency is acceptable.
Amazon Aurora (pgvector): Ideal when applications must retain and leverage an existing relational PostgreSQL database infrastructure.
Amazon Neptune Analytics: Designed for GraphRAG, multi-hop relationship traversals, and uncovering complex entity connections (e.g., fraud networks) using nodes and edges.
4. Safety, Governance & Guardrails
Bedrock Guardrails: Acts as an independent safety net placed outside the raw model inference path to filter both inputs and outputs.
PII Masking: Automatically detects and redacts sensitive data (like SSNs, phone numbers, or credit cards) from user inputs and model outputs.
Contextual Grounding Checks: Evaluates hallucination risks by mathematically verifying whether the generated response is strictly supported by the retrieved Knowledge Base chunks.
5. Asynchronous Integration & Auditing Plane
Amazon EventBridge: A decoupled, multi-target content-based router utilizing PutEvents (fire-and-forget). Use it to trigger parallel, non-blocking post-processing tasks instantly.
Amazon SQS: Serves as a shock absorber and rate-limiting queue. Used to buffer high-throughput traffic spikes and securely route flagged, low-confidence interactions into a dedicated compliance review queue without crashing downstream worker systems.
6. Orchestration & Framework Patterns
Bedrock Flows: Deterministic (Node-Based). Use this when the execution path must follow a rigid, 100% predictable, step-by-step sequence (e.g., strict regulatory compliance or audit pipelines).
Bedrock Agents: Non-Deterministic (ReAct Pattern). Use this when the LLM needs to dynamically reason and choose which tools or Lambda-backed APIs to invoke at runtime based on user intent.
7. Platform Selection: Build vs. Buy Matrix
Amazon Q Business: Fully managed, turn-key enterprise search application featuring built-in native connectors. Choose this for rapid employee search solutions requiring zero custom pipeline building.
Amazon Bedrock: Managed serverless APIs for frontier models (Claude, Llama, Titan) paired with custom RAG, Guardrails, and Agents.
SageMaker JumpStart / Training: Provides deep custom fine-tuning (LoRA, RLHF) and full infrastructure control over underlying GPU instances.
8. GenAI Ops, Observability & Monitoring
AWS X-Ray: Provides end-to-end distributed tracing across AppSync → Lambda → Bedrock KB → Vector Store → LLM to isolate latency bottlenecks.
Bedrock Model Invocation Logs: Captures raw user prompts and model completions, persisting them to Amazon S3 or CloudWatch Logs for audit and compliance tracking.
Model Evaluation: Utilizes automated metrics (such as ROUGE/BLEU for text overlap and custom toxicity scripts) alongside structured human evaluation loops.