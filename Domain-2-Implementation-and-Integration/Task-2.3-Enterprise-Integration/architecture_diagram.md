========================================================================================
                TASK 2.3: THREE CALLERS, ONE GOVERNED PATH TO THE MODEL
========================================================================================

THREE WAYS IN - the lanes run in parallel; each caller gets the endpoint type that suits it.

[ LANE A - CONSUMER & WORKFORCE CLIENTS  (public internet) ]
  +-- (A1) Web · mobile · branch staff
  |       Cognito user pools hold the external consumer identities; Amplify DataStore
  |       keeps branch staff working offline and resolves conflicts on reconnect
  |
  +-- (A2) AWS WAF
  |       rate-based, geo-match and SQL injection rules — a malicious script or an
  |       infinite loop is capped before it becomes a token bill
  |
  +-- (A3) API Gateway — EDGE-OPTIMIZED  ·  AppSync
  |       CloudFront fronts the API because these users are spread across 30+
  |       countries · custom domain ai.bank.com · AppSync VTL resolvers map GraphQL
  |       straight to a model payload

[ LANE B - LEGACY CORE SYSTEMS  (private network) ]
  +-- (B1) Legacy core banking system
  |       SOAP · EBCDIC · fixed-width files · JMS/AMQP — holds the records, cannot be
  |       rewritten
  |
  +-- (B2) Private transport — pick one
  |       - Direct Connect — synchronous; BGP policies prioritize inference so bulk
  |         sync cannot block it
  |       - Amazon MQ — chosen only because the legacy side already speaks JMS/AMQP
  |       - AWS Glue · AppFlow — bulk and SaaS sync; job bookmarks replay only new
  |         records
  |
  +-- (B3) Transit Gateway · Network Firewall
  |       black hole routes guarantee no path from Dev into Prod · stateful inspection
  |       and domain filtering stop exfiltration to unapproved hosts
  |
  +-- (B4) API Gateway — REGIONAL
  |       the caller is already inside the network, so CloudFront would add a hop and
  |       buy nothing · mapping template converts XML/SOAP → JSON
  |
  +-- (B5) Lambda adapter
  |       EBCDIC → UTF-8, fixed-width → JSON · reserved concurrency caps the blast
  |       radius, provisioned kills cold starts

[ LANE C - EXTERNAL WEBHOOKS  (public endpoint) ]
  +-- (C1) Partner & SaaS callbacks
  |       loan approvals, settlement notices — delivered at-least-once, so duplicates
  |       are guaranteed, not exceptional
  |
  +-- (C2) AWS WAF
  |       rate-based rules; a looping sender cannot run up the bill
  |
  +-- (C3) API Gateway — REGIONAL
  |       a webhook handler has no global audience to serve — the sender is a machine,
  |       not a travelling user

****************************************************************************************
  Endpoint type follows the caller, not the workload.  EDGE-OPTIMIZED puts a
  CloudFront distribution in front when users are scattered worldwide (lane A).
  REGIONAL is right when the caller is already in-region — a legacy system on Direct
  Connect, or a webhook sender (lanes B and C).
****************************************************************************************

            \        |        /
             v       v       v

[ NORMALIZE ]
  +-- (1) EventBridge
  |       pattern matching drops events that do not qualify · input transformer folds
  |       three callers' payloads — customerId, customer_id, cust.id — into one shape,
  |       so nothing downstream parses three dialects
  |       DLQ: Processing failure routes to a dead-letter queue. Financial events are
  |       audit-relevant, so nothing is ever silently dropped.
           |
           v
[ SHORT-CIRCUIT GATES — ANSWER BEFORE SPENDING A TOKEN ]
  +-- (2) DynamoDB idempotency check (TTL)
  |       seen this event ID before? this is what makes lane C's at-least-once
  |       delivery safe — a duplicate returns the stored result instead of re-invoking
  |       and double-billing
  +-- (3) Response cache — API Gateway / ElastiCache / database
  |       has this exact prompt already been answered for anyone? invalidated by TTL,
  |       by an EventBridge event on data change, or write-through
  |       >>> HIT at either gate: Returned without invoking a model — zero tokens billed, millisecond latency
  |           skips every step in between, straight to response mapping
           |
           v
[ THE GENAI GATEWAY ]
  +-- (4) ALL THREE LANES FUNNEL THROUGH THE GENAI GATEWAY
  |       - Usage plan + API key per team: Team A, Team B, Team C each get their own
  |         throttle; one team's runaway bug cannot exhaust everyone's capacity
  |       - Verified Permissions (Cedar): department, clearance and business context
  |         — the claims the JWT already carries
  |       - Centralized guardrails: one safety filter for every caller and every
  |         team; no application can route around it
  |       - Model routing, fallback & cost attribution: swap models without touching
  |         a single team's code; bill tokens back per team
  |       NOTE: Identity was established out-of-band, before the request — not here.
  |       IAM Identity Center federates the corporate directory for workforce users,
  |       so 50,000+ accounts are never re-created, and in lane A the Cognito pre-
  |       token Lambda injects department, clearance and region into the JWT. By the
  |       time WAF sees the packet those claims already exist, which is why Cedar can
  |       evaluate them at this step.
           |
           v
[ PRIVATE PATH TO THE MODEL ]
  +-- (5) PrivateLink endpoint policy
  |       never the public internet · bedrock:InvokeModel on claude-* only — no fine-
  |       tuning, no deletion
           |
           v
[ ORCHESTRATION ]
  +-- (6) Step Functions · SQS FIFO
  |       Parallel: fraud + balance + limit checks at once · Map: the same check
  |       across 1,000 transactions · MessageGroupId = customer-id keeps one
  |       customer's steps in order
           |
           v
[ EXECUTION — OR MOVE THE MODEL TO THE DATA ]
  +-- (7a) Amazon Bedrock / Amazon SageMaker
  |       the default path, in-region
  |   -- or --
  +-- (7b) AWS Outposts · Local Zones · Wavelength
  |       when the data legally cannot leave the premises, the city or the carrier
  |       network · filter, anonymize or tokenize before any payload crosses a border
           |
           v
[ RETURN PATH — EACH CALLER GETS ITS OWN SHAPE BACK ]
  +-- (8) API Gateway response mapping
  |       lane B gets JSON → XML/SOAP, the exact shape it already expects · lanes A
  |       and C get JSON unchanged
  +-- (9) Write back
  |       store the response in cache and the event ID in DynamoDB, so the next
  |       duplicate exits at the gates above
  +-- (10) Back to the caller
  |       the legacy core is never modified and never aware a foundation model was
  |       involved

========================================================================================
CROSS-CUTTING (applies at every step above)
========================================================================================
  +-- CloudTrail: immutable audit trail of every step above
  +-- KMS multi-region keys: one decryptable key across 30+ jurisdictions, auto-rotated
  +-- CloudWatch + X-Ray: composite alarms; sample 5% normal, 100% of errors
  +-- Control Tower: blocks deployments that break data residency
========================================================================================
