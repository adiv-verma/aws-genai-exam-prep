graph TD
    %% 1. Triggers & Entry
    subgraph Triggers ["1. Triggers & Enterprise Entry"]
        Event[Enterprise Event / User Request] --> SF[AWS Step Functions Orchestrator]
    end

    %% 2. Safeguards Layer
    subgraph Safeguards ["2. Safeguards & Control Layer (Step Functions)"]
        SF --> StopCond[Stopping Conditions: Max 10 Loops / 5 Mins]
        StopCond --> Timeouts[Timeout & Graceful Termination]
        Timeouts --> CB[CloudWatch Alarms & Circuit Breakers]
    end

    %% 3. Model Coordination & Reasoning
    subgraph Reasoning ["3. Model Coordination & Reasoning Layer"]
        CB --> DynSelect[Dynamic Model Selector / Task Router]
        DynSelect --> Claude[Claude 3 Sonnet: Complex Reasoning / CoT]
        DynSelect --> Titan[Titan Text / Smaller Models: Reports]
        DynSelect --> Ensemble[Model Ensembles: Weighted Averaging via Lambda]
        
        Claude --> CoT[Step-by-Step Workflow CoT Engine]
    end

    %% 4. Memory Hierarchy
    subgraph Memory ["4. Three-Tier Memory Hierarchy"]
        CoT -. "Operational" .-> ElastiCache[ElastiCache / DynamoDB TTL (Session State)]
        CoT -. "Tactical" .-> DDB_Tac[DynamoDB (Active Disruptions & Scratchpad)]
        CoT -. "Strategic" .-> S3_KB[S3 / Knowledge Base (Historical Patterns)]
    end

    %% 5. Human-in-the-Loop
    subgraph HITL ["5. Collaborative AI & Human-in-the-Loop"]
        CoT --> CheckRisk{Risk & Confidence Check}
        CheckRisk -- "< 0.7 or High Risk" --> WaitToken[Step Functions Wait Token State (Paused)]
        WaitToken --> Reviewer[Human Reviewer Portal]
        Reviewer --> Feedback[DynamoDB GSIs: Store Corrections & Feedback]
    end

    %% 6. Tool Integrations & MCP
    subgraph Tools ["6. Intelligent Tool Integrations & MCP"]
        CoT --> AG[Action Groups / OpenAPI Schemas]
        AG --> ValLambda[Lambda: Input & Business Rule Validation]
        ValLambda --> IAM[IAM Least Privilege Boundary]

        IAM --> LambdaMCP[AWS Lambda: Lightweight Calculators / MCP Servers]
        IAM --> ECS[Amazon ECS: Heavy Simulations / Optimizers]
        IAM --> APIGW[API Gateway: Legacy ERP & Supplier APIs]
    end

    %% Final Output
    CoT --> Output[Optimized Supply Chain Decision / Action Executed]