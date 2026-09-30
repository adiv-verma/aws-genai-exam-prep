[ User / Client Application ]
              │
              ▼
   [ Response Cache (Redis / ElastiCache) ] ──(Cache Hit)──► Return Instant Answer
              │
         (Cache Miss)
              │
              ▼
    [ Step Functions Router ] ──(Async / Bulk)──► [ Amazon SQS Queue ] ──► [ Asynchronous Consumer ]
              │                                                                     │
              ├──────(Direct / Fast Check)──────┐                                   ▼
              │                                 │                         [ Bedrock / SageMaker ]
              ▼                                 ▼
   [ Small Model (Cascading) ]       [ Bedrock On-Demand / Provisioned ]
              │                                 │
     (Confidence Check)                         │
     ├── High ──► Return Answer ──────────────┤
     └── Low  ──► Escalate to:                 │
                     │                          │
                     ▼                          │
         [ SageMaker Custom Endpoint / ]        │
         [ Bedrock Custom Model Import ] ◄──────┘
                     │
                     ▼
         [ Store Response in Cache ]


