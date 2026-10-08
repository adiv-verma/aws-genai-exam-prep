========================================================================================
                    TASK 2.3: ENTERPRISE INTEGRATION ARCHITECTURE 
========================================================================================

[ CLIENTS & LEGACY SOURCES ]
  ├── Web / Mobile Apps (Cognito Auth)
  ├── Branch Staff (Amplify DataStore / Offline Sync)
  └── Legacy Systems (SOAP, EBCDIC, Fixed-Width Files, JMS/AMQP via Amazon MQ)
           │
           ▼
[ PERIMETER & NETWORK CONNECTIVITY LAYER ]
  ├── AWS WAF (Rate Limiting & Billing Attack Protection)
  ├── Transit Gateway (Domain Isolation: Dev / Test / Prod via Black Hole Routes)
  ├── Direct Connect / PrivateLink (Secure Enterprise-to-Cloud Routing)
  └── Network Firewall (Stateful Inspection & Domain Filtering)
           │
           ▼
[ ENTRY & TRANSLATION LAYER ]
  ├── API Gateway (Regional / Edge-optimized endpoints)
  ├── Lambda Adapters (Protocol conversion: SOAP -> JSON, Fixed-width -> UTF-8)
  └── EventBridge (Event filtering & Input Transformers)
           │
           ▼
========================================================================================
                                THE GENAI GATEWAY (CENTRAL HUB)
========================================================================================
  ├── Usage Plans & Throttling (Per-team API keys and rate limits)
  ├── Webhook Idempotency (DynamoDB TTL check to prevent duplicate billing)
  ├── Multi-Level Caching (API Gateway, ElastiCache, Database)
  ├── Cost Tracking & Allocation (Token consumption logs per team)
  ├── Centralized Guardrails & Safety Filters
  └── Model Routing & Fallback Logic (Switching models without code changes)
           │
           ▼
[ SECURITY & AUTHORIZATION LAYERS ]
  ├── IAM Identity Center (Workforce / Active Directory Federation)
  ├── Cognito Pre-Token Lambda Triggers (Injecting enterprise roles into JWT)
  ├── IAM Verified Permissions & Cedar Engine (Fine-grained policy checks)
  └── KMS Multi-Region Keys (Compliant encryption & automatic rotation)
           │
           ▼
[ ORCHESTRATION & WORKFLOW LAYER ]
  ├── Step Functions (Parallel & Map states for batch operations)
  ├── SQS FIFO & Message Group IDs (Maintaining transactional order per customer ID)
  └── AWS Glue & AppFlow (Incremental data sync via Job Bookmarks & SaaS connectors)
           │
           ▼
[ MODEL EXECUTION TARGETS ]
  ├── Cloud Region: Amazon Bedrock (Claude, etc.) / Amazon SageMaker
  └── Edge Infrastructure: AWS Outposts (On-prem), Local Zones, or Wavelength (5G)
           │
           ▼
[ GOVERNANCE, OBSERVABILITY & CI/CD ]
  ├── Control Tower (Enforcing Data Residency & Organization-level guardrails)
  ├── CloudWatch Composite Alarms & X-Ray (Smart sampling & complex failure detection)
  ├── CloudTrail (Immutable API call audit logging)
  └── CodePipeline (GenAI-specific stages: Model Evaluation, Security Scanning, Approval Gates)
========================================================================================