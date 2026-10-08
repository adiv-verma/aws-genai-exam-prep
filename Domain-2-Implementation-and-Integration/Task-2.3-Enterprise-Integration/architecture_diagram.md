========================================================================================
                        TASK 2.3: ONE LEGACY REQUEST, END TO END
========================================================================================

[ ORIGIN ]
  +-- (1) Legacy core banking system
  |       SOAP · EBCDIC · fixed-width files · JMS/AMQP — holds the records, cannot be
  |       rewritten
           |
           v
[ TRANSPORT — THREE WAYS IN ]
  +-- (2a) Direct Connect  --  synchronous, real-time
  |       dedicated link; BGP policies prioritize inference traffic so bulk sync
  |       cannot block it
  +-- (2b) Amazon MQ  --  asynchronous messaging
  |       managed ActiveMQ / RabbitMQ, active/standby — chosen only because the legacy
  |       side already speaks JMS/AMQP
  +-- (2c) AWS Glue / AppFlow  --  bulk + SaaS sync
  |       job bookmarks replay only new records · pre-built connectors for Salesforce,
  |       ServiceNow, Slack
           |
           v
[ NETWORK PERIMETER ]
  +-- (3) Transit Gateway
  |       Dev / Test / Prod isolation; black hole routes guarantee no path can exist
  |       from Dev into Prod
  +-- (4) Network Firewall
  |       stateful rule groups inspect FM-to-legacy traffic; domain filtering blocks
  |       exfiltration to unapproved hosts
  +-- (5) AWS WAF
  |       rate-based rules stop a runaway loop or malicious script before it becomes a
  |       seven-figure token bill
           |
           v
[ TRANSLATION — LEGACY DIALECT TO JSON ]
  +-- (6) API Gateway
  |       mapping template converts XML/SOAP → JSON · regional or edge-optimized ·
  |       custom domain ai.bank.com
  +-- (7) Lambda adapter
  |       EBCDIC → UTF-8, fixed-width → JSON · reserved concurrency caps the blast
  |       radius, provisioned kills cold starts
  +-- (8) EventBridge
  |       pattern matching drops events that do not qualify · input transformer
  |       normalizes customerId / customer_id / cust.id
  |       DLQ: Processing failure routes to a dead-letter queue. Financial events are
  |       audit-relevant, so nothing is ever silently dropped.
           |
           v
[ SHORT-CIRCUIT GATES — ANSWER BEFORE SPENDING A TOKEN ]
  +-- (9) DynamoDB idempotency check (TTL)
  |       seen this event ID before? webhooks are at-least-once, so duplicates are
  |       expected, not exceptional
  +-- (10) Response cache — API Gateway / ElastiCache / database
  |       has this exact prompt already been answered for anyone?
  |       >>> HIT at either gate: Returned without invoking a model — zero tokens billed, millisecond latency
  |           jumps straight to the response-mapping step below
           |
           v
[ THE GENAI GATEWAY ]
  +-- (11) ALL TRAFFIC FUNNELS THROUGH THE GENAI GATEWAY
  |       - Usage plan + API key: per-team throttle; one team's bug cannot exhaust everyone's capacity
  |       - Verified Permissions (Cedar): department, clearance and business context — the claims the JWT already carries
  |       - Centralized guardrails: one safety filter for every team; no application can route around it
  |       - Model routing, fallback & cost attribution: swap models without touching a single team's code; bill tokens back per team
  |       NOTE: Identity was established out-of-band, at login — not here. IAM
  |       Identity Center federates the corporate directory, so 50,000+ accounts are
  |       never re-created, and the Cognito pre-token Lambda injects department,
  |       clearance and region into the JWT. By the time WAF sees the packet those
  |       claims already exist, which is why Cedar can evaluate them at this step.
           |
           v
[ PRIVATE PATH TO THE MODEL ]
  +-- (12) PrivateLink endpoint policy
  |       never the public internet · bedrock:InvokeModel on claude-* only — no fine-
  |       tuning, no deletion
           |
           v
[ ORCHESTRATION ]
  +-- (13) Step Functions · SQS FIFO
  |       Parallel: fraud + balance + limit checks at once · Map: the same check
  |       across 1,000 transactions · MessageGroupId = customer-id keeps one
  |       customer's steps in order
           |
           v
[ EXECUTION — OR MOVE THE MODEL TO THE DATA ]
  +-- (14a) Amazon Bedrock / Amazon SageMaker
  |       the default path, in-region
  |   -- or --
  +-- (14b) AWS Outposts · Local Zones · Wavelength
  |       when the data legally cannot leave the premises, the city or the carrier
  |       network · filter, anonymize or tokenize before any payload crosses a border
           |
           v
[ RETURN PATH ]
  +-- (15) API Gateway response mapping
  |       JSON → XML/SOAP — back into the exact shape the legacy system already
  |       expects
  +-- (16) Write back
  |       store the response in cache and the event ID in DynamoDB, so the next
  |       duplicate exits at the gates above
  +-- (17) Legacy core banking system
  |       receives XML/SOAP · never modified, never aware a foundation model was
  |       involved

========================================================================================
CROSS-CUTTING (applies at every step above)
========================================================================================
  +-- CloudTrail: immutable audit trail of every step above
  +-- KMS multi-region keys: one decryptable key across 30+ jurisdictions, auto-rotated
  +-- CloudWatch + X-Ray: composite alarms; sample 5% normal, 100% of errors
  +-- Control Tower: blocks deployments that break data residency
========================================================================================
