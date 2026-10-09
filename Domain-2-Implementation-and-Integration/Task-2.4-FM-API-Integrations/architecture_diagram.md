flowchart TD
    %% Clients & Edge Layer
    Client[Client App / Mobile / Tablet] -->|HTTPS / SSE / WebSocket| APIGW[API Gateway\n- Request Validation (max_tokens, Schema)\n- Custom Headers / x-model-preference]

    %% Routing & Configuration Layer
    APIGW -->|Check Rules| AppConfig[AWS AppConfig / SSM\n- Static Configuration & Feature Flags]
    APIGW -->|Evaluate Content| SFN[AWS Step Functions\n- Choice States & Content-Based Routing\n- Parallel Execution for Multi-Specialty]

    %% Metrics & Decision Layer
    SFN -->|Query Historical Data| Timestream[Amazon Timestream & DynamoDB\n- Metric-Based Routing & Performance Tracking]

    %% Model Invocation Layer (With Multi-Level Throttling & Fallbacks)
    Timestream --> Router{Model Routing Decision}
    
    Router -->|High-End Specialised FM| FM1[Specialised Medical Model\n- Route-Level Limits: 50 RPS]
    Router -->|General Enterprise FM| FM2[General Model + Prompts\n- Route-Level Limits: 500 RPS]

    %% Resilient Fallback Chain
    FM1 -.->|Low Confidence / Failure| Cascade[Model Cascading\n- Pass Metadata & Partial Context]
    Cascade --> FM2
    FM2 -.->|Model Degradation| RAG[RAG over Hospital Knowledge Base]
    RAG -.->|Critical Function Fallback| RuleBased[Rule-Based System]

    %% Asynchronous Processing & Background SQS
    Client -.->|Async Request / Post-Encounter| SQS[Amazon SQS Queue\n- Visibility Timeout: 10 mins]
    SQS --> Worker[Lambda / Background Workers\n- Connection Pool: 10-20 connections]
    Worker --> FM2

    %% Monitoring, Tracing & A/B Testing
    FM1 & FM2 --> XRay[AWS X-Ray / CloudWatch\n- Subsegments: Preprocessing, Invocation, Postprocessing\n- Annotations & p50/p90/p99 Metrics]
    XRay --> AB[A/B Testing & Timestream Feedback Loop]

    style APIGW fill:#f9f,stroke:#333,stroke-width:2px
    style SFN fill:#bbf,stroke:#333,stroke-width:2px
    style Router fill:#bfb,stroke:#333,stroke-width:2px
    style Cascade fill:#ff9,stroke:#333,stroke-width:2px
    style RAG fill:#fbb,stroke:#333,stroke-width:2px