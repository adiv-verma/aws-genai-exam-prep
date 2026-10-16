[ Healthcare Users / Applications ]
                                       │
                                       ▼
                  ┌──────────────────────────────────────────┐
                  │          VPC Boundary (Dedicated)         │
                  │                                          │
                  │   [ Private Subnet ]                     │
                  │   ┌──────────────────────────────────┐   │
                  │   │ Application / Processing Lambda  │   │
                  │   └──────────────────────────────────┘   │
                  │                    │                     │
                  │                    ▼                     │
                  │   ┌──────────────────────────────────┐   │
                  │   │ Pre-Processing & Sanitization    │   │
                  │   │  • PII Detection (Comprehend)    │   │
                  │   │  • De-identification Lambda      │   │
                  │   │    - Tokenization Mapping        │   │
                  │   │    - Format-Preserving Enc.      │   │
                  │   │    - Differential Privacy        │   │
                  │   │  • Quality Control Check         │   │
                  │   └──────────────────────────────────┘   │
                  │                    │                     │
                  │                    ▼                     │
                  │   ┌──────────────────────────────────┐   │
                  │   │ VPC Endpoints (AWS PrivateLink)  │   │
                  │   └──────────────────────────────────┘   │
                  └──────────────┬────────────┬──────────────┘
                                 │            │
            (Private AWS Network)│            │(Private AWS Network)
                                 ▼            ▼
         ┌─────────────────────────┐        ┌─────────────────────────┐
         │ Interface VPC Endpoint  │        │ Gateway VPC Endpoint    │
         │  • Security Groups      │        │  • Route Table Entry    │
         └────────────┬────────────┘        └────────────┬────────────┘
                      │                                  │
                      ▼                                  ▼
      ┌───────────────────────────────┐  ┌───────────────────────────────┐
      │ Amazon Bedrock                │  │ Amazon S3 / Data Storage      │
      │  • Guardrails (PII/Topics)    │  │  • Macie (S3 PII Scan)        │
      │  • Contextual Access Controls │  │  • Lake Formation Controls    │
      │  • Zero Model Training        │  │    (Column/Row/Cell level)    │
      │  • KMS Encryption             │  │  • Lifecycle Retention Rules  │
      └───────────────────────────────┘  └───────────────────────────────┘
                      │                                  │
                      └────────────────┬─────────────────┘
                                       │
                                       ▼
                     ┌──────────────────────────────────┐
                     │ Continuous Audit & Monitoring    │
                     │  • CloudTrail (API Audit Logs)   │
                     │  • CloudWatch (Insights/Alarms)  │
                     │  • GuardDuty (Threat Detection)  │
                     │  • Security Hub (Centralized)    │
                     └──────────────────────────────────┘