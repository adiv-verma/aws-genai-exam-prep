Domain 3, Task 3.3 — Step 1: Compliance Frameworks (Detailed Notes)
1. SageMaker Model Cards
Definition & Concept: A SageMaker Model Card serves as a central repository for model metadata throughout its lifecycle. It functions as both a "birth certificate" (documenting intent, origin, and setup) and a "report card" (documenting evaluation scores, bias, and compliance readiness).
Core Standard Contents:
Model Overview: Intended business use cases, operational constraints, and explicitly unsupported uses.
Data Lineage: Characteristics, schema, volume, and potential limitations/biases of training and validation datasets.
Evaluation Metrics: Baseline performance metrics across test split distributions and specialized stress-testing scenarios.
Risk & Guardrails: Known operational limitations, failure modes, safety boundaries, and recommended human oversight practices.
Financial & Regulatory Additions:
SEC / FINRA Documentation: Explicit audit fields documenting regulatory compliance checks and risk assessments.
Demographic Fairness & Explainability: Fairness scores across sensitive demographic groups and explainability metrics (e.g., feature attribution scores) justifying output logic.
Version Control & Lifecycle Management: Built-in SDK/API lifecycle methods (create_model_card(), update_model_card(), export_model_card()) to handle state transitions from creation to approval.
Programmatic Generation via CI/CD: Manual documentation quickly becomes outdated when models are retrained. To keep cards synchronized with production, SageMaker Model Cards are generated and updated automatically inside automated CI/CD deployment pipelines. Metrics and artifacts are programmatically extracted directly from SageMaker Training Jobs, Processing Jobs, and Inference Endpoints without manual human intervention.
2. SageMaker ML Lineage Tracking
Definition & Purpose: Tracks the end-to-end lineage of an ML workflow to reconstruct how a specific model version was built, covering the exact training data, source code, execution parameters, and output artifacts.
DAG (Directed Acyclic Graph) Architecture: Lineage is modeled as a graph composed of three core entity types connected by Associations:
Artifacts (create_artifact()): Physical or digital entities, such as S3 URI references to raw datasets, trained model weights, evaluation metrics files, or ECR Docker container images.
Actions (create_action()): Computational work or processing steps performed, such as ETL data preparation jobs, SageMaker training jobs, or model transformation steps.
Contexts (create_context()): Logical groupings that tie actions and artifacts together, such as an active SageMaker Endpoint, an MLflow/SageMaker Experiment, or a pipeline execution run.
Custom Entities & AWS Glue Integration:
Custom Entity Linking: While SageMaker automatically records lineage for native SageMaker components, external components (e.g., third-party data pipelines or external API calls) must be linked explicitly using custom Lineage entities.
Data vs. Model Lineage: Model lineage tracks how the model was trained, whereas AWS Glue tracks data lineage (how raw data was transformed before reaching the ML step).
AWS Glue Provenance: Glue ETL jobs leverage custom job parameters, source-to-target schema mappings stored in the Glue Data Catalog, and the DynamicFrame class to maintain precise field-level data transformations.
3. Metadata Tagging & Access Controls
Standardized Tagging Framework: Applies consistent metadata across all AWS resources using the TagResource API to establish governance scope. Example taxonomy:
DataSensitivity: confidential
RegulatoryScope: SEC
DataProvider: Bloomberg
ModelVersion: v3
Jurisdiction: EU
Tag-Based Access Control (TBAC): IAM policies restrict access based on resource tags (e.g., granting production model access only to authorized compliance roles).
Preventative Governance via SCPs: AWS Organizations Service Control Policies (SCPs) and AWS Tag Policies strictly enforce tagging policies at the account boundary. Any API call attempting to create an untagged resource is automatically denied before deployment.
4. CloudWatch Logs — Decision Logging & Audit Trails
Financial Advisory Decision Logging: Regulators require institutions to justify why a specific recommendation was selected over another. CloudWatch Logs must record comprehensive transaction payloads:
Input & Decision Parameters: Full prompt payload, user risk context, market inputs, and decision criteria.
Model Outputs & Confidence Scores: Recommendation outcome alongside calculated confidence thresholds.
Alternative Recommendations: Crucial for compliance. Logs must capture candidate recommendations that were evaluated but rejected, proving why the primary recommendation was chosen.
Audit Trail Requirements:
End-to-End Traceability: Unbroken tracking chain from initial user query to the final financial advisory response.
Human Oversight Tracking: Logging explicit human-in-the-loop interventions, approvals, or manual overrides to verify operational human oversight.
Correlation IDs: Unique IDs injected into requests to trace a single transaction across distributed microservices and API gateways.
Structured Logging & Metrics: Logs are emitted in structured JSON format to allow for direct querying via CloudWatch Logs Insights. Metric Filters extract specific patterns from log streams to trigger real-time CloudWatch custom governance metrics and alerts.


Domain 3, Task 3.3 — Step 2: Data Source Tracking (Detailed Notes)
1. Glue Data Catalog — Source Registration & Licensing
Centralized Metadata Repository: Serves as the authoritative registry for all financial datasets, market feeds, and internal document repositories used by AI models and RAG systems.
Automated Schema & Format Classification: Utilizes Glue Crawlers equipped with custom classifiers to ingest and parse specialized financial file formats. Programmatic query APIs (GetTables, GetDatabases) enable automated system integration.
Licensing & Provider Governance:
Metadata Categorization: Data assets are explicitly tagged and categorized by Data Type, Provider (e.g., Bloomberg, Refinitiv, internal research), and Jurisdiction (e.g., US, EU, APAC).
Licensing Rights Management: Tracks legally permissible usage constraints per data vendor—specifically recording whether a dataset can be used for LLM pre-training, fine-tuning, or dynamic RAG prompt injection.
Data Reliability Scoring: Maintains data quality and reliability metrics within catalog metadata to weigh downstream confidence scores.
2. CloudTrail Configuration — Data Access Auditing
Multi-Region Logging: CloudTrail trails must be configured across all active AWS Regions to guarantee complete audit coverage without unmonitored blind spots.
Management vs. Data Events:
Management Events: Log control plane operations (e.g., CreateBucket, UpdateModel) and are enabled by default.
Data Events (Critical Exam Distinction): Log data plane access operations (e.g., S3 GetObject, PutObject). Data events are OFF by default due to high volume and cost. They must be explicitly enabled to audit precisely which S3 objects or documents were read during training, fine-tuning, or RAG context construction.
Audit Reporting via Athena: CloudTrail logs stored in S3 are queried using Amazon Athena SQL queries to generate point-in-time compliance and access audit reports.
3. Cross-Account Lineage
Enterprise Multi-Account Architectures: In enterprise environments, datasets frequently reside in a centralized Data Lake account, while SageMaker model training or Bedrock inference runs in separate workload accounts.
Lineage Persistence: To prevent lineage breakage across account boundaries, systems utilize the SageMaker AddAssociation API paired with cross-account IAM roles and explicitly qualified Resource ARNs (Amazon Resource Names).
4. Data Versioning & Exact Reproducibility
Regulatory Requirement: Regulators (e.g., SEC/FINRA) often mandate that a financial firm reproduce the exact AI output generated on a specific date in the past.
Versioning Mechanisms:
S3 Versioning & Lifecycle Policies: Preserves immutable versions of unstructured raw documents, PDFs, and training files over time.
SageMaker Feature Store Time Travel: Allows point-in-time queries on structured feature tables (e.g., "What was customer X's credit score feature on March 1, 2024?").
The Reproducibility Guarantee: Executing the Same Model Version against the Same Data Version guarantees the Same Output Result.
5. Source Attribution & Output Auditing
Attribution in AI Responses: AI outputs track and store references to the underlying data sources that influenced a given recommendation.
Weighted Confidence Scores: Recommendations built upon lower-reliability or unverified data sources are programmatically assigned lower confidence scores.
Practical RAG Attribution Boundary: While exact sentence-to-chunk token mapping inside an LLM is non-deterministic, regulatory compliance requires tracking and logging the exact data chunks included in the LLM prompt context window.
Auditing the Attribution Engine: The attribution mechanism itself is subject to continuous audit through:
Verification Workflows: Testing attribution accuracy against known ground truths.
Completeness Audits: Identifying un-attributed or orphan output responses.
Remediation Processes: Fixing gaps in context tracking and logging pipelines.


Domain 3, Task 3.3 — Step 3: Organisational Governance Systems (Detailed Notes)
1. Three Layers of Control (Permission Hierarchy)
Enforces multi-layered access boundaries and governance limits across large-scale enterprise environments:
AWS Organizations Level — Service Control Policies (SCPs):
Permission Ceiling: Sets the maximum allowable permissions across AWS accounts. SCPs never grant permissions; they only restrict/deny.
Inviolable Restrictions: An account administrator (even root in a member account) cannot bypass an SCP limit.
Governance Examples: Enforcing region restrictions (e.g., prohibiting Bedrock deployments outside us-east-1), denying creation of untagged resources, or restricting model customization jobs strictly to approved accounts.
Account Level — IAM Policies:
Grants explicit identity-based or role-based permissions to users, services, and execution roles.
Service Level — Resource Policies:
Controls access directly on individual resources (e.g., S3 Bucket Policies, KMS Key Policies, SageMaker Endpoint Policies).
2. Automated Approval Workflows & Separation of Duties
AWS Step Functions Orchestration: Automated governance workflows enforce strict validation gates before promoting models to production:
Governance Metrics Check→Compliance Checks→Approval Tracking (DynamoDB)→Promote / Reject
Automated Stage Gates:
Bias Metrics Check: Validates whether pre/post-training bias metrics fall within legal thresholds.
Model Card Completeness: Verifies 100% completion of mandatory documentation fields.
Evaluation Thresholds: Confirms that benchmark and accuracy tests pass required targets.
Human-in-the-Loop Approval: Requires explicit approval signatures prior to deployment.
Separation of Duties: Enforces organizational compliance rules preventing the developer who built/trained a model from approving its deployment to production.
3. Centralized Model Dashboard & Governance at Scale
SageMaker Model Dashboard: Provides a single-pane-of-glass operational view across hundreds of production models, tracking performance, drift status, and compliance posture.
Automated Alerting & Eventing: Integrates create_monitoring_schedule() with Amazon EventBridge to automatically publish alerts when models deviate from governance rules.
Quantitative Governance Metrics: Replaces static documentation with measurable operational CloudWatch metrics:
Percentage of active models with up-to-date SageMaker Model Cards.
Percentage of models operating within approved bias thresholds.
Days elapsed since the last formal model re-evaluation.
Count and tracking of non-compliant/untagged resources.
4. SageMaker Clarify — Bias & Explainability Metrics
Measuring demographic fairness is a legal requirement under financial regulations (e.g., fair lending laws). SageMaker Clarify computes three primary quantitative bias metrics:
DPPL (Difference in Positive Proportions in Labels):
Measures the gap in the proportion of positive outcomes between a favored demographic group (q) and an un-favored group (a).
DPPL=q−a
DI (Disparate Impact):
Measures the ratio of positive outcomes received by an un-favored group relative to a favored group.
DI= 
q
a
​	
 
Rule of Thumb: Values significantly below 0.8 indicate potential disparate impact/bias.
DCR (Difference in Conditional Rejection):
Measures the gap in rejection rates between demographic groups after conditioning on baseline qualification factors (e.g., comparing rejection rates for applicants with equal credit scores).
Stages of Bias Analysis:
Pre-training Bias: Evaluates whether historical training datasets contain inherent baseline imbalances or demographic skew.
Post-training Bias: Evaluates whether the trained model's predictions output biased decisions (even if trained on seemingly balanced data).


Domain 3, Task 3.3 — Step 4: Continuous Monitoring & Advanced Controls (Detailed Notes)
1. SageMaker Model Monitor & Drift Types
Baseline Establishment: Uses constraint suggestion algorithms during training to build a statistical baseline representing expected input schemas and statistical distributions.
Four Core Monitoring Modules:
Data Quality Drift: Detects changes in data structure, schema violations, null values, or statistical shifts in input features.
Model Quality Drift: Evaluates ground truth labels against endpoint predictions to detect degradation in performance metrics (e.g., F1 score, MSE).
Bias Drift (SageMaker Clarify Integration): Evaluates whether model predictions exhibit demographic bias over time due to real-world population shifts.
Feature Attribution Drift: Measures whether the relative importance/weighting of input features driving predictions has shifted compared to the baseline.
Jensen-Shannon (JS) Divergence: Used to calculate distance/divergence between baseline probability distributions and production prediction distributions. Requires precise threshold calibration to balance false alarms against un-alerted real drift.
2. Automated Remediation & The Closed Governance Loop
Real-time Event-driven Mitigation: When a monitoring alarm fires due to drift or bias threshold violations, waiting for human manual review introduces compliance risk.
Remediation Pipeline:
Model Monitor Alarm→Amazon EventBridge Rule→AWS Lambda / Step Functions→Automated Rollback / Traffic Shift
Automated Actions: Triggers automated Blue/Green endpoint traffic shifts, falling back to a known compliant model version or cutting off live traffic entirely while notifying compliance officers.
3. Token-Level PII Redaction
Endpoint Custom Handlers: Implemented using pre-processing and post-processing handlers on SageMaker endpoints or middleware wrappers around Bedrock calls.
Redaction Techniques: Combined usage of deterministic pattern matching (regex for SSNs, credit card numbers) and semantic Named Entity Recognition (NER) ML models for broader contextual PII detection.
Token-Level Precision: Rather than blocking or rejecting the entire prompt/response, sensitive tokens are stripped or masked while leaving the non-sensitive response intact and functional.
Example: "Account 4532-1234 balance is $5,000" → "Account [REDACTED] balance is $5,000"
4. Output Filtering & Misuse Monitoring
Bedrock Guardrails & Policy Filters: Applied as a defensive layer to block unsafe content, restrict topics, prevent PII leakage, and mitigate hallucinated outputs. Combined with prompt engineering and RAG context limits.
Misuse Anomaly Detection: Continuous tracking of usage patterns to identify malicious activity, such as:
Sudden spikes in query volume (100× normal baseline).
Off-hours access anomalies or systematic jailbreak/probing attempts.
Unusual automated batch extraction patterns.
5. Automated Compliance Reporting
Pipeline Architecture:
CloudWatch Custom Governance Metrics→AWS Glue / QuickSight Data Ingestion→Amazon QuickSight Compliance Dashboards
Regulatory Readiness: Keeps compliance audit reports in a state of continuous generation rather than requiring weeks of manual log collation at the end of each fiscal quarter.