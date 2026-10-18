+---------------------------------------------------+
                                  |            DEVELOPMENT & TESTING PHASE            |
                                  +---------------------------------------------------+
                                                            |
                                                            v
+-----------------------+     +---------------------------------------------------------------+
| Evaluation Datasets   | --> |                  Amazon Bedrock Evaluations                   |
| & Custom Rubrics      |     +---------------------------------------------------------------+
| (S3 Version Controlled|     |  * LLM-as-a-Judge (Claude 3 Opus evaluating Generator)        |
+-----------------------+     |  * BYOI (Bedrock, SageMaker, On-Prem)                         |
                              |  * Dimension Scoring (Relevance, Accuracy, Compliance, Tone)  |
                              +---------------------------------------------------------------+
                                                            |
                                                            v
                                  +---------------------------------------------------+
                                  |              CI/CD QUALITY GATES                  |
                                  +---------------------------------------------------+
                                                            |
                                                            v
                              +---------------------------------------------------------------+
                              |                      AWS CodePipeline                         |
                              |  [ Daily Continuous Eval via AWS Step Functions ]            |
                              |                                                               |
                              |  Quality Gate: Compliance >= 99.8% & Accuracy >= Threshold?   |
                              +---------------------------------------------------------------+
                                        /                                           \
                              NO (Fail) /                                             \ YES (Pass)
                                       v                                               v
                             +-------------------+                           +--------------------+
                             |  RELEASE BLOCKED  |                           | SHADOW DEPLOYMENT  |
                             | (Rollback/Alert)  |                           | (Real traffic,     |
                             +-------------------+                           |  discard output)   |
                                                                             +--------------------+
                                                                                       |
                                                                                       v
                                                                             +--------------------+
                                                                             |   CANARY DEPLOY    |
                                                                             | (Small % traffic)  |
                                                                             +--------------------+
                                                                                       |
                                                                                       v
                                                                             +--------------------+
                                                                             | FULL PRODUCTION    |
                                                                             +--------------------+
                                                                                       |
                                                                                       v
                                  +---------------------------------------------------+
                                  |              PRODUCTION MONITORING                |
                                  +---------------------------------------------------+
                                                            |
                                 +--------------------------+--------------------------+
                                 |                                                     |
                                 v                                                     v
      +--------------------------------------------------+     +------------------------------------------------+
      |            RAG & Agent Monitoring                |     |              User Feedback Ingestion           |
      +--------------------------------------------------+     +------------------------------------------------+
      | * Retrieve-Only vs Retrieve-and-Generate         |     | * Kinesis Data Streams (Real-time interactions)|
      | * Chunking, Vector DB & Citation Coverage        |     | * SageMaker Ground Truth (Expert Review)       |
      | * Bedrock Agent Tool & Reasoning Evaluation      |     | * Amazon Comprehend (Sentiment Analysis)       |
      +--------------------------------------------------+     +------------------------------------------------+
                                 |                                                     |
                                 +--------------------------+--------------------------+
                                                            |
                                                            v
                                      +-------------------------------------------+
                                      |          Amazon QuickSight                |
                                      | (Role-Based Dashboards & Trend Analytics) |
                                      +-------------------------------------------+