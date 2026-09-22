# AWS Step Functions Workflows

AWS Step Functions coordinates multiple AWS services into serverless workflows, expressed as state machines defined in the Amazon States Language, so that multi-step processes can be built without writing custom orchestration code.

## Standard versus Express workflows

Step Functions offers two workflow types. Standard workflows are designed for long-running, durable, auditable processes — they can run for up to a year, provide exactly-once execution semantics, and retain a full execution history for every run, which is visible in the console for debugging. Express workflows are designed for high-volume, short-duration event-processing workloads — they can run for up to five minutes, support at-least-once execution semantics, and are billed based on the number of executions and their duration rather than per state transition, making them dramatically cheaper for workloads that fire thousands or millions of times per day.

## State types

A state machine is built from a small set of state types. Task states invoke work, most commonly a Lambda function or a direct AWS SDK integration with another service. Choice states implement branching logic based on the current execution's data. Parallel states run a fixed set of branches concurrently and wait for all of them to complete. Map states iterate over an array of items, running the same set of states once per item, either sequentially or with a distributed, concurrent execution mode for large arrays. Wait states pause execution for a specified duration or until a specified timestamp, without consuming compute resources while waiting.

## Error handling and retries

Every task state can define retry behavior, specifying which error types to retry, an interval between attempts, a backoff rate, and a maximum number of attempts, all without any custom code. If retries are exhausted or an error type is not configured for retry, a catch block can route execution to a fallback state, allowing a workflow to degrade gracefully — for example, sending a notification and stopping cleanly rather than leaving the workflow in an unclear failed state.

## Long-running and asynchronous integrations

For work that takes longer than a single Lambda invocation should reasonably block on, such as a transcription job or a batch data export, Step Functions supports a callback pattern where a task state pauses and waits for an external process to report completion via a task token, rather than a Lambda function polling in a loop. This avoids tying up compute resources and Lambda's maximum execution duration while a slow, asynchronous job runs to completion elsewhere.

## Orchestrating parallel and multi-part work

The Map state's distributed mode is specifically built for fanning out large amounts of independent work — for example, running the same processing logic across thousands of files in S3, or executing several independent sub-queries derived from a single complex user question and merging their results afterward. Distributed Map can process up to tens of millions of items in a single execution while Step Functions manages concurrency limits and per-item error handling automatically.
