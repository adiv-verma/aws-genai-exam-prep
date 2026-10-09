[ Client / Amplify UI ] (ARIA Live Regions, Similarity Caching)
         │
         ▼ (WebSocket / HTTPS + Content Filtering Middleware)
[ Amazon API Gateway ] (Rate Limiting, JWT Auth)
         │
         ├──────────────────────────────────────────┐
         ▼                                          ▼
[ Amazon EventBridge ] (Reactive Trigger)     [ AWS Lambda ] (CRM Sentiment, 4-Tier Timeouts, Circuit Breaker)
         │                                          │
         ▼                                          ▼
[ AWS Step Functions ] (Declarative Workflow)  [ Amazon Q Business / Q Developer ]
   ├── Parallel Chunk Processing                    │
   ├── Bedrock Data Automation (BDA)                ▼
   └── Quality Threshold Gates ───────────> [ Enterprise Data & CRM / Audit Logs ]
                                                    │
                                                    ▼
                             [ CloudWatch Logs Insights & AWS X-Ray Observability ]