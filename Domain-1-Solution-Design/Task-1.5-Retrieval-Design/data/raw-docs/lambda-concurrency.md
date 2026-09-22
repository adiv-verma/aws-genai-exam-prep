# AWS Lambda Concurrency and Scaling

AWS Lambda scales automatically by running separate instances of a function to handle concurrent invocations, but understanding how concurrency is allocated and limited matters for both cost control and avoiding throttling under load.

## Concurrency fundamentals

Concurrency is the number of requests a function is serving at any given time. Each concurrent execution runs in its own isolated environment. When a new request arrives and no idle environment is available, Lambda creates a new one — this is a cold start, which adds initialization latency. An account has a regional concurrency limit (a soft quota, typically 1,000 by default and increasable via a support request) shared across all functions in that account and region unless reserved concurrency is configured.

## Reserved concurrency

Reserved concurrency guarantees a function a fixed portion of the account's concurrency pool and simultaneously caps how high that function can scale. Setting reserved concurrency to zero effectively throttles a function completely, which is a common technique for disabling a function during an incident without deleting it. Reserved concurrency is useful for protecting downstream resources — for example, a Lambda function writing to a relational database with a limited connection pool should be capped so it cannot open more concurrent connections than the database can handle.

## Provisioned concurrency

Provisioned concurrency keeps a specified number of execution environments initialized and ready to respond, eliminating cold starts for that portion of traffic. It is billed for the time it is enabled regardless of whether it is invoked, which distinguishes it from Lambda's normal pay-per-invocation pricing. Provisioned concurrency is typically applied to latency-sensitive, user-facing APIs with predictable traffic patterns, often paired with Application Auto Scaling to adjust the provisioned amount on a schedule that matches known traffic peaks.

## Throttling and retries

When a function receives more concurrent requests than its available concurrency allows, additional invocations are throttled and return a 429 TooManyRequestsException. Synchronous invocations (such as through API Gateway) surface this error directly to the caller, while asynchronous invocations (such as S3 event notifications) are automatically retried by Lambda with exponential backoff before being sent to a configured dead-letter queue or on-failure destination if retries are exhausted. Event source mappings for stream-based sources like Kinesis or DynamoDB Streams handle throttling differently, retrying the same batch until it succeeds or the data expires from the stream.

## Cost implications

On-demand concurrency scaling has no direct cost beyond the standard per-invocation and per-GB-second billing, but under-provisioned reserved concurrency can cause cascading throttling failures that are expensive in terms of downstream retries and customer impact. Provisioned concurrency has a direct, continuous cost proportional to the number of environments kept warm, so it should be sized against actual measured traffic rather than worst-case peak estimates.
