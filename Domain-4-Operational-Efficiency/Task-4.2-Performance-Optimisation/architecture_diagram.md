graph TD
    %% Use Case 1: Pre-computation / Caching
    subgraph UseCase1[Use Case 1: Pre-computation & Caching (Low Latency)]
        UC1_User[User Client] -->|Predictable Query| UC1_API[API Gateway]
        UC1_API -->|Lookup| UC1_Lambda[AWS Lambda]
        UC1_Lambda <-->|Sub-ms| UC1_ElastiCache[Amazon ElastiCache]
        UC1_Lambda <-->|Single-digit ms| UC1_DynamoDB[Amazon DynamoDB]
        UC1_Lambda .->|Asynchronous pre-population| UC1_PrePopLambda[Pre-population Lambda]
    end

    %% Use Case 2: Response Streaming
    subgraph UseCase2[Use Case 2: Response Streaming (Low Perceived Latency)]
        UC2_User[User Client] -->|Stream Request| UC2_App[Application Backend]
        UC2_App -->|InvokeStream| UC2_Bedrock[Amazon Bedrock]
        UC2_Bedrock -.->|Server-Sent Events (SSE)| UC2_App
        UC2_App -.->|Tokens Stream| UC2_User
    end

    %% Use Case 3: Parallel Requests
    subgraph UseCase3[Use Case 3: Parallel Requests (AWS Step Functions)]
        UC3_API[API Gateway] -->|Workflow Start| UC3_SF[AWS Step Functions]
        
        subgraph ParallelState[Parallel State / Map State]
            UC3_SF -->|Invoke (Parallel)| UC3_CallA[Bedrock Call A]
            UC3_SF -->|Invoke (Parallel)| UC3_CallB[Bedrock Call B]
            UC3_SF -->|Invoke (Parallel)| UC3_CallC[Bedrock Call C]
        end
        ParallelState -->|Aggregate| UC3_SF
    end

    %% Use Case 4: Advanced RAG Optimization
    subgraph UseCase4[Use Case 4: RAG & Retrieval Optimization]
        UC4_Query[User Query] -->|Invoke| UC4_LambdaPre[Lambda Preprocessing]
        UC4_LambdaPre -->|Spellcheck/Normalise/Expand| UC4_LambdaPre
        UC4_LambdaPre -->|Vector Search| UC4_VectorDB[Vector Database (e.g., OpenSearch)]
        
        subgraph VectorDBEngine[Vector DB Internals]
            UC4_HNSW[HNSW Index (Speed/Memory)] -.-> UC4_Search
            UC4_IVF[IVF Index (Capacity/Memory)] -.-> UC4_Search
            UC4_Search[Search Execution]
        end
        
        UC4_VectorDB -->|Raw Results| UC4_LambdaRerank[Lambda Custom Reranking]
        UC4_LambdaRerank -->|Final Result Set| UC4_App
    end

    %% Use Case 5: GenAI Autoscaling & Provisioned Throughput
    subgraph UseCase5[Use Case 5: Efficient Resource Allocation]
        UC5_LB[Load Balancer / SQS] -->|Route Traffic| UC5_AutoScaling[EC2 Auto Scaling Group]
        
        subgraph ASG_Instances[SageMaker / EC2 Instances]
            UC5_AutoScaling --> UC5_Model[SageMaker Endpoint / Inferentia]
        end

        UC5_CW[CloudWatch] -->|Monitor Token Length/Utilisation| UC5_AutoScaling
        UC5_CW -.->|Predictive Scaling Input| UC5_AutoScaling
        
        subgraph DedicatedCap[Dedicated Capacity]
            UC5_PT[Provisioned Throughput (Bedrock)]
        end
    end

    %% Monitoring, Benchmarking, and A/B Testing
    subgraph MonitoringAB[Monitoring & A/B Testing]
        M_App[GenAI Application] -->|Send Metrics/Logs| M_CW[Amazon CloudWatch]
        M_CW -->|Dashboard/Insights| M_Admin[Admin]
        M_App <-->|A/B Variant Control| M_Evidently[CloudWatch Evidently]
    end

    %% Style definitions
    classDef awsService fill:#fff,stroke:#232f3e,stroke-width:1px,rx:5,ry:5,color:#232f3e,font-size:10pt;
    classDef primaryComponent fill:#e6f3ff,stroke:#0056b3,stroke-width:2px,rx:5,ry:5,color:#003d7e,font-weight:bold,font-size:12pt;
    classDef subgroupBox fill:#f9f9f9,stroke:#aeaeae,stroke-dasharray: 5 5,rx:5,ry:5,color:#545454,font-size:9pt;

    class UC1_API,UC1_Lambda,UC1_ElastiCache,UC1_DynamoDB,UC2_API,UC2_LambdaStream,UC2_Bedrock,UC3_API,UC3_SF,UC3_CallA,UC3_CallB,UC3_CallC,UC4_LambdaPre,UC4_VectorDB,UC4_LambdaRerank,UC5_LB,UC5_AutoScaling,UC5_Model,UC5_CW,UC5_PT,M_CW,M_Evidently awsService;
    class UseCase1,UseCase2,UseCase3,UseCase4,UseCase5,MonitoringAB primaryComponent;
    class ParallelState,VectorDBEngine,ASG_Instances,DedicatedCap subgroupBox;