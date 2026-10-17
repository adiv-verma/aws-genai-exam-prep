1. End-to-End AWS System Architecture
[ Patient / Clinician UI ]
           │
           │ (1) HTTPS / Streaming API Request
           ▼
   [ Amazon CloudFront ]
           │
           ▼
    [ Amazon API Gateway ]
           │
           │ (2) Pre-Processing Policy Enforcement
           ▼
   ┌──────────────────────────────────────────────────────────┐
   │ AWS Lambda (Pre-Inference Guardrail & Input Sanitizer)    │
   │  ├─ Redact PII (AWS Comprehend Medical)                  │
   │  └─ Enforce Input Bedrock Guardrails (Topic/Content)     │
   └──────────────────────────┬───────────────────────────────┘
                              │
                              │ (3) InvokeAgent (enableTrace=true)
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Amazon Bedrock Agent Loop                          │
│                                                                         │
│   ┌────────────────────────┐      (4) Vector Search & Citation        │
│   │ ReAct Reasoning Engine │ ──────────────────────────────────┐        │
│   └───────────┬────────────┘                                   │        │
│               │                                                ▼        │
│               │ (5) Tool Invocation           ┌───────────────────────┐ │
│               ▼                               │ Knowledge Bases for   │ │
│  ┌────────────────────────┐                   │ Amazon Bedrock        │ │
│  │ Lambda Custom Tools    │                   │ (OpenSearch Serverless│ │
│  │ (Clinical Rules Engine)│                   │  Medical Vector DB)   │ │
│  └────────────────────────┘                   └───────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               │ (6) Post-Processing & Output Compliance
                               ▼
   ┌──────────────────────────────────────────────────────────┐
   │ AWS Lambda (Post-Inference Validator & Grounding Check)  │
   │  ├─ Contextual Grounding Check (Hallucination Detection)  │
   │  ├─ Output Bedrock Guardrails (Fairness & Bias Filters)   │
   │  └─ Medical Literacy Adaptation Check                    │
   └──────────────────────────┬───────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               │ (7) Async Observability &   │
               │     Compliance Logging      │
               ▼                             ▼
┌────────────────────────────┐ ┌─────────────────────────────────────────┐
│     Amazon CloudWatch      │ │           AWS Audit Manager             │
│  ├─ Trace Metrics & Logs   │ │  (GenAI Best Practices Framework)       │
│  ├─ Confidence Metrics     │ │  └─ Automatically Gathers Audit Evidence│
│  └─ Disparity Impact Alarms│ └─────────────────────────────────────────┘
└──────────────┬─────────────┘
               │
               │ (8) Continuous Fairness & Evaluation Pipeline
               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 Continuous Evaluation Pipeline (CI/CD)                  │
│                                                                         │
│  ┌────────────────────────┐       (9) Auto-Update Metadata              │
│  │ Amazon SageMaker AI    │ ───────────────────────────────────┐        │
│  │ (LLM-as-a-Judge Bias   │                                    │        │
│  │  & Counterfactual Tests│                                    ▼        │
│  └────────────────────────┘                   ┌───────────────────────┐ │
│                                               │ Bedrock Model Cards   │ │
│                                               │ (Demographic Baselines│ │
│                                               │  & Known Biases)      │ │
│                                               └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘