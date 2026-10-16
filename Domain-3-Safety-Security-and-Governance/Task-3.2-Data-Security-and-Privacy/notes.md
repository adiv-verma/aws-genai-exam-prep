Domain 3, Task 3.2: Data Security & Privacy Controls
Part 1 — Protected AI Environments (Revision Notes)
1. Network Isolation & Architecture
Core Challenge
Amazon Bedrock is a public AWS service by default. In highly regulated domains like healthcare (HIPAA compliance), routing inference traffic or prompt data over the public internet is unacceptable due to data leakage and exfiltration risks.
Solution: AWS PrivateLink & VPC Endpoints
All traffic between your workload components (e.g., Lambda, ECS, EC2) and AWS GenAI services must stay entirely within the AWS internal backbone network using VPC Endpoints.
[ Private Subnet ]                                 [ AWS Backbone ]
+----------------------+     PrivateLink           +-------------------+
| App / Lambda Server  | ------------------------> | Amazon Bedrock    |
| (No Internet Egress) |   (VPC Endpoint Traffic)  | / Comprehend / S3 |
+----------------------+                           +-------------------+
Types of VPC Endpoints
Endpoint Type	Supported Services	Deployment Mechanism	Security & Governance Controls
Interface Endpoint	Amazon Bedrock, Amazon Comprehend, and most AWS services	Creates an Elastic Network Interface (ENI) with a private IP inside your specific VPC Subnet.	Governed directly by Security Groups (stateful firewalls) and Network ACLs (NACLs).
Gateway Endpoint	Amazon S3 & Amazon DynamoDB only	Exists at the VPC level as a Target Entry in the VPC Route Table (does NOT consume subnet IPs or create an ENI).	Governed via Route Tables and VPC Endpoint Policies (no Security Groups attached).
Target Architecture Checklist
Dedicated VPC: Isolated AWS environment for the healthcare AI workload.
Private Subnets: All compute, database, and model invocation layers reside in private subnets with zero direct internet routes (no IGW / NAT Gateways attached unless strictly required).
Security Groups: Enforce strict, stateful port-level traffic rules between application tiers.
Network ACLs (NACLs): Provide a secondary stateless defense layer at the subnet boundary.
Strict Egress Filtering: Prevents compromised compute components from exfiltrating patient data outside the VPC perimeter.
2. Fine-Grained Access Control (IAM & Lake Formation)
A. Identity and Access Management (IAM) for Bedrock
Enforces the principle of least privilege across three main operational axes:
                          ┌─ Restrict to Specific MODELS (e.g., Anthropic Claude 3 Sonnet)
                          │
IAM Policy Restrictions ──┼─ Restrict to Specific FEATURES (e.g., Provisioned Throughput vs. On-Demand)
                          │
                          └─ Restrict to Specific OPERATIONS (e.g., Allow InvokeModel, Deny Customization)
Resource-Based Policies: Applied directly to Bedrock resources (e.g., Knowledge Bases, Custom Models) to control which principals can access them.
Condition Keys: Used within policies to enforce strict runtime constraints (e.g., requiring requests to originate from a specific VPC Endpoint ID aws:sourceVpce, enforcing KMS encryption keys, or checking tag matching).
Access Models:
RBAC (Role-Based Access Control): Permissions assigned strictly based on a static role (e.g., Doctor, Nurse, Billing Administrator).
ABAC (Attribute-Based Access Control): Permissions evaluated dynamically based on attributes (e.g., Department, Clearance Level, Assigned Patient ID). Offers greater scalability without creating new IAM policies for every new condition.
B. AWS Lake Formation Governance
While IAM grants bucket-level or database-level permissions, Lake Formation enforces fine-grained data access controls inside tables for datasets used in training, fine-tuning, or RAG grounding.
+-------------------+-----------------------------------------------------------------------+
| Control Level     | Healthcare Example                                                    |
+-------------------+-----------------------------------------------------------------------+
| Column-Level      | Doctors see "Diagnosis" and "Treatment Plan", but NOT "SSN" / "DOB".  |
| Row-Level         | Doctors can query ONLY rows corresponding to their assigned patients. |
| Cell-Level        | Hides specific sensitive values in individual cells dynamically.     |
+-------------------+-----------------------------------------------------------------------+
Data Catalogs: Centralized metadata repositories that continuously track, index, and enforce fine-grained access over AI-related datasets across the organization.
3. Monitoring, Auditing & Threat Detection
Continuous monitoring ensures full traceability of all generative AI interactions for HIPAA compliance.
[ Bedrock API Calls ] ──> Amazon CloudTrail (Full API Audit Logs)
                       ──> CloudWatch Logs Insights (Query & Log Analysis)
                       ──> Amazon GuardDuty (Threat Detection & Anomaly Alerts)
                       ──> AWS Security Hub (Centralized Findings & Automated Remediation)
AWS CloudTrail: Captures a complete, immutable audit trail of every Bedrock API invocation (e.g., InvokeModel, RetrieveAndGenerate), including requester identity and timestamp.
Amazon CloudWatch Logs Insights: Enables fast querying and pattern matching across API access logs to identify policy violations or unusual query behavior.
Amazon GuardDuty: Employs threat detection and machine learning to identify suspicious data access patterns, credential compromise, or unusual API usage.
AWS Security Hub: Aggregates and correlates security findings from GuardDuty, Macie, and Inspector.
Automated Remediation & Log Retention: Triggers automated AWS Lambda workflows to isolate resources upon security alerts while maintaining log retention policies aligned with healthcare regulatory standards (e.g., 3–7 years).



Domain 3, Task 3.2: Data Security & Privacy Controls
Part 2 — Privacy-Preserving Systems (Revision Notes)
1. PII Detection (Two Services, Two Places)
Amazon Comprehend:
Operates on text in real-time (at request time) to detect 25+ types of PII.
Comprehend Medical: The healthcare-specific variant that detects PHI (Protected Health Information), extracts medical entities from unstructured text, and classifies sensitive clinical information.
Amazon Macie:
Operates on data stored in Amazon S3.
Automatically discovers and classifies sensitive data using built-in and custom data identifiers tailored for organization-specific formats.
2. Bedrock's Native Privacy Guarantees
Zero Model Training on Customer Data: Customer prompts, inputs, and outputs are never used to train or improve Bedrock's foundation models. This is a foundational compliance requirement for healthcare workloads.
Encryption: Full encryption in transit and at rest for all data processed by foundation models.
Secure Knowledge Bases: Provides secure vector storage and retrieval mechanisms for grounded generation.
3. Bedrock Guardrails for Privacy
PII Filters: Automatically strip or mask sensitive information from model inputs and outputs.
Custom Topic Filters: Block specific undesirable or non-compliant categories.
Contextual Controls: Filtering adapts dynamically based on the user's role and access level. For example, the same foundation model can serve a doctor and a billing clerk under completely different guardrail configurations.
4. S3 Lifecycle & Retention as Compliance
Automated Retention Enforcement: Implements lifecycle policies to transition data to cold storage or execute automated deletions aligned with regulatory mandates:
Patient Records: 7 years (regulatory requirement)
Access Logs: 3 years
Temporary Processing Data: 30 days
Audit Trails for Deletion: Compliant deletion requires more than just deleting data—you must maintain a verifiable audit trail proving when and how the deletion occurred.
5. Encryption & Processing Pipeline
AWS KMS Integration: Enforces encryption at rest, key rotation policies, and strict access controls on encryption keys.
Pipeline Architecture:
Pre-processing Lambda sanitizes inputs → real-time PII detection and redaction → separate logging of PII detection events.
Note: Logging what was detected and redacted is a separate compliance requirement from performing the redaction itself.


Domain 3, Task 3.2: Data Security & Privacy Controls
Part 3 — Privacy-Focused AI Systems & De-identification (Revision Notes)
1. Record-Level Masking Strategies
When PII/PHI is detected, deleting it entirely destroys prompt context for the LLM, while leaving it intact violates HIPAA compliance. Masking strategies preserve semantic utility while obscuring identity.
Technique	Mechanism	Example	Reversible?	Primary Use Case & Context Impact
Redaction	Irreversibly strips sensitive values	"John Smith" → "[NAME]"	No	Least Context Retained. Model cannot infer whether two mentions refer to the same individual. Choose when sensitive data must simply be erased.
Tokenization	Replaces sensitive data with a unique surrogate token	"John Smith" → "PATIENT_8472"	Yes (via Secure Token Mapping Table)	Consistent References Preserved. Enables cross-border/cross-domain tracking or recovery of original values later.
Pseudonymization	Replaces sensitive data with realistic fake values	"John Smith" → "Patient A"	Yes (via Mapping Table)	Most Context Retained. Reads as natural text, allowing the model to process input with maximum semantic fluency.
Format-Preserving Encryption (FPE)	Encrypts value while preserving exact length and shape	4532-1234-5678-9010 → 8821-9945-2210-3387	Yes	Structure Retained. Essential when legacy systems or strict downstream parsers validate field formats.
2. Dataset-Level Anonymization
When handling entire datasets for RAG Knowledge Bases, fine-tuning, or model evaluation, individual record masking is insufficient. Dataset-level anonymization prevents re-identification across broader populations:
Generalization: Reduces data precision by grouping specific values into broader intervals.
Example: Age 34→30–40; ZIP 90210→902; Date 2024-03-15→March 2024.
Perturbation: Adds small statistical variations to numerical values so aggregate properties remain consistent while individual records are modified.
Example: Salary $85,000→$84,200.
Synthetic Data Generation: Learns the mathematical distribution of a real dataset to generate an entirely artificial dataset.
Advantage: Safest model (no real individuals exist in the data).
Challenge: High complexity in preserving exact statistical relationships without introducing bias.
3. Advanced Mathematical Privacy Controls
A. Differential Privacy
Prevents attackers from inferring an individual's inclusion in a dataset by comparing aggregate queries (e.g., querying total cardiology patients before and after one patient is discharged).
Mechanism: Adds controlled randomized statistical noise to query outputs (e.g., actual count =500, returned count =502,498,or 501).
Privacy Budget (ϵ): Tracks privacy loss over time. Every query consumes a portion of the budget. Without a budget, repeated queries average out the noise to reveal the true underlying value. Once depleted, further queries are denied.
Core Trade-off: Direct balance between privacy and utility (↑Noise=↑Privacy,↓Utility).
B. K-Anonymity
Ensures that any individual's quasi-identifiers (e.g., Age, ZIP, Gender) in a released dataset are identical to at least k−1 other individuals.
Group Size≥k
Example: Generalizing Age to 30–40 and ZIP to 902 results in 8 matching individuals for a specific diagnosis record. If k=5, k-anonymity is satisfied because no single person can be uniquely isolated.
4. End-to-End De-identification Architecture
[ Raw PHI / Patient Records ]
             │
             ▼
[ Anonymization AWS Lambda ]
   ├── Tokenization Service (Mapping Table)
   ├── Format-Preserving Encryption Engine
   ├── Differential Privacy Engine
   └── De-identification Workflow Orchestrator
             │
             ▼
[ Data Quality Control Check ]  <── CRITICAL STEP: Validates utility vs. anonymization
             │
             ▼
[ Anonymized S3 Data Bucket ]
             │
             ▼
[ Amazon Bedrock Models ] <── Guardrails (Content Filtering, Contextual Controls)
Exam Warning: Over-anonymizing data to the point where it destroys downstream model utility is a primary architectural failure mode. Anonymization pipelines must include a Data Quality Control step to verify that data utility is preserved before pushing to Bedrock.