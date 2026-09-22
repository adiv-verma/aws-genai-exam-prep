# Amazon DynamoDB Capacity Modes

DynamoDB offers two capacity modes that determine how read and write throughput is provisioned and billed: on-demand and provisioned. Choosing between them affects both cost predictability and how the table behaves under sudden traffic spikes.

## On-demand capacity mode

On-demand mode charges per request rather than for pre-allocated throughput, and DynamoDB automatically scales to accommodate traffic without any capacity planning. It is well suited to workloads with unpredictable or highly variable traffic, new applications where request patterns are not yet known, and workloads with sudden, sharp spikes for which pre-provisioning would be guesswork. On-demand tables can absorb roughly double their previous peak traffic immediately, and continue scaling from there as sustained traffic increases.

## Provisioned capacity mode

Provisioned mode requires specifying read capacity units (RCUs) and write capacity units (WCUs) ahead of time, and is billed for that reserved throughput whether or not it is fully used. It is more cost-effective than on-demand for steady, predictable traffic, especially when combined with auto scaling policies that adjust provisioned capacity within a defined min/max range based on a target utilization percentage. Provisioned mode also supports reserved capacity purchases for further savings on workloads with well-understood, long-term throughput needs.

## Throttling behavior

In provisioned mode, requests that exceed the currently provisioned RCUs or WCUs are throttled and return a ProvisionedThroughputExceededException, even briefly, unless burst capacity (a short-lived buffer DynamoDB retains from unused past capacity) absorbs the spike. On-demand mode also has account-level and table-level throughput ceilings, but they scale automatically rather than requiring manual intervention, so throttling under on-demand is rarer and generally only occurs during extremely abrupt, unprecedented traffic increases.

## Switching between modes

A table can switch between on-demand and provisioned capacity mode once every 24 hours, which makes it possible to start a new application in on-demand mode to observe real traffic patterns, then move to provisioned mode with informed RCU/WCU settings once the workload is well understood. Global secondary indexes inherit capacity settings independently in provisioned mode, so each index must be sized for its own query pattern, not just the base table's.

## Choosing a mode

As a rule of thumb, on-demand is the safer default for new or spiky workloads because it removes the risk of under-provisioning and the resulting throttling, at a higher per-request cost. Provisioned mode with auto scaling becomes more cost-effective once traffic is steady and well characterized, typically saving money at sustained, predictable request volumes.
