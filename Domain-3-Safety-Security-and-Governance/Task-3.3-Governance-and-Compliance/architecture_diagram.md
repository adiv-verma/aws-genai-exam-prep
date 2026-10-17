graph TD
    %% --- External Drivers ---
    Regulators[fa:fa-balance-scale Regulators<br/>(SEC, FINRA, EU)] -.->|Audit Mandates| GRC_Metrics

    %% --- 1. Organisation Governance Layer (SCPs/IAM) ---
    subgraph Layer1 [Layer 1: Organisation & Account Governance]
        SCP[AWS Organizations<br/>SCPs & Tag Policies]
        IAM[IAM Policies &<br/>Permission Boundaries]
        SCP -->|Enforce Tagging / Region Blocks| SM
        IAM -->|Separation of Duties<br/>(Builder != Approver)| Pipeline
    end

    %% --- 2. Data Source Tracking Layer (Glue/CloudTrail) ---
    subgraph Layer2 [Layer 2: Data Source Tracking & Lineage]
        S3_Data[(S3 Data Lake<br/>Financial Docs & Market Feeds)]
        
        Glue_Catalog[fa:fa-database AWS Glue Data Catalog<br/>(Source Registry, Jurisdiction,<br/>Licensing, Schema)]
        Glue_Crawler[AWS Glue Crawlers]
        
        Glue_Job[fa:fa-cogs AWS Glue ETL Jobs<br/>(DynamicFrame,<br/>Custom Job Parameters)]

        CT_Data[fa:fa-history AWS CloudTrail<br/>(DATA Event Logging ON)]
        Athena[Amazon Athena<br/>(Audit Queries)]

        %% Flows
        S3_Data -.->|Read| Glue_Crawler
        S3_Data <-.->|Data Events| CT_Data
        Glue_Crawler -->|Catalog Metadata| Glue_Catalog
        Glue_Job -->|Data Lineage| Glue_Catalog
        Glue_Job -->|Data Lineage Associations| SM_Lineage
        CT_Data -->|Query Audit Trails| Athena
    end

    %% --- 3. Model Development & Deployment Pipeline Layer ---
    subgraph Layer3 [Layer 3: Compliance Framework Pipeline (Custom / SM)]
        CICD[fa:fa-code-branch CI/CD Pipeline<br/>(CodePipeline)]
        
        SM_Train[SageMaker<br/>Training / Fine-Tuning]
        SM_Clarify_Pre[fa:fa-chart-bar SageMaker Clarify<br/>(Pre-Training Bias)]
        
        SM_Lineage[fa:fa-project-diagram SageMaker ML Lineage<br/>(Artifacts, Actions, Contexts,<br/>Associations)]
        
        SM_Card[fa:fa-id-card SageMaker Model Cards<br/>(Purpose, Data, Performance,<br/>Limitations)]
        
        S3_Version[S3 Versioning +<br/>SM Feature Store Time Travel]

        %% Approval Step Function
        StepFunc[fa:fa-check-double AWS Step Functions<br/>Approval Workflow]
        DDb_Audit[fa:fa-file-signature Amazon DynamoDB<br/>(Approval Audit Trail)]

        %% Flows
        CICD -->|Trigger| SM_Train
        S3_Data -->|Input| SM_Train
        S3_Data <-->|Versioning/Reproducibility| S3_Version
        SM_Train <-->|Pre-training Bias| SM_Clarify_Pre
        
        SM_Train -.->|Automatic Lineage| SM_Lineage
        SM_Train -.->|Metrics/Parameters| SM_Card
        
        CICD -->|Execute| StepFunc
        StepFunc <-->|Verify| SM_Clarify_Pre
        StepFunc <-->|Verify| SM_Card
        StepFunc <-->|Log Approved Signature| DDb_Audit
    end

    %% --- 4. Advanced Controls & Foundation Models (Bedrock) ---
    subgraph Layer4 [Layer 4: Bedrock / FM Governance]
        Bedrock[fa:fa-rocket AWS Bedrock<br/>(Foundation Models)]
        KnowledgeB[Bedrock Knowledge Bases<br/>(RAG Data Sources)]
        Guardrails[fa:fa-shield-alt Bedrock Guardrails<br/>(Content Filters / PII)]

        %% Flows
        S3_Data -->|Ingest| KnowledgeB
        KnowledgeB -->|Context Chunks| Bedrock
        Bedrock <-->|Apply Policies| Guardrails
    end

    %% --- 5. Continuous Monitoring Layer ---
    subgraph Layer5 [Layer 5: Continuous Monitoring]
        SM_Endpoint[fa:fa-server SageMaker<br/>Inference Endpoint]
        
        SM_Monitor[fa:fa-heartbeat SageMaker<br/>Model Monitor]
        SM_Clarify_Post[SageMaker Clarify<br/>(Post-Training/Bias Drift)]
        
        Handler_PII[fa:fa-mask Endpoint Handlers<br/>(PII Redaction pre/post)]

        %% Remediation
        EB[fa:fa-bell Amazon EventBridge]
        Lambda_Rem[fa:fa-magic AWS Lambda<br/>Remediation (Rollback/Shift)]

        %% Flows
        SM_Train -->|Deploy| SM_Endpoint
        SM_Endpoint <-->|Apply NER/Regex| Handler_PII
        Handler_PII <-->|Continuously Monitor<br/>(Data/Model Quality, Bias,<br/>Feature Attribution)| SM_Monitor
        SM_Monitor <-->|Bias/Attribution| SM_Clarify_Post
        S3_Data -->|Baseline| SM_Monitor
        
        SM_Monitor -->|Alert| EB
        EB -->|Trigger| Lambda_Rem
        Lambda_Rem -->|Execute Remediation| SM_Endpoint
    end

    %% --- 6. Analytics & Reporting Layer ---
    subgraph Layer6 [Layer 6: Analytics & Reporting]
        CW_Logs[fa:fa-file-alt Amazon CloudWatch Logs<br/>(Alternatives, Timestamps,<br/>Correlation IDs)]
        CW_Metrics[fa:fa-tachometer-alt Amazon CloudWatch Metrics]
        QS_Dashboard[fa:fa-chart-pie Amazon QuickSight<br/>(Compliance Dashboards<br/>& Reports)]
        
        %% Flow
        Handler_PII -->|Decision Logs<br/>(JSON, Alternatives)| CW_Logs
        SM_Monitor -->|Metrics| CW_Metrics
        CW_Logs -->|Filter Metrics| CW_Metrics
        CW_Metrics -->|Visualize Governance| QS_Dashboard
        Glue_Catalog -->|Data Catalog Metrics| QS_Dashboard
        QS_Dashboard --> GRC_Metrics[fa:fa-file-contract Quarterly<br/>Compliance Reports]
    end

    %% --- Connective Flows ---
    Pipeline[Deployable] -.-> StepFunc
    Bedrock -.->|Lineage Context| SM_Lineage
    Bedrock -.->|Decision Logs| CW_Logs

    %% Styling
    classDef blue fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef green fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef orange fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef purple fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef red fill:#ffebee,stroke:#c62828,stroke-width:2px;
    classDef grey fill:#f5f5f5,stroke:#616161,stroke-width:1px,stroke-dasharray: 5 5;

    class Layer1 grey;
    class Layer2 blue;
    class Layer3 green;
    class Layer4 purple;
    class Layer5 orange;
    class Layer6 red;