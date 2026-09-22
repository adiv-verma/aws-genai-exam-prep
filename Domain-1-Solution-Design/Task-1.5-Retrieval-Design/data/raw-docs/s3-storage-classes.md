# Amazon S3 Storage Classes

Amazon S3 offers a range of storage classes designed for different access patterns and cost profiles. Choosing the right class for a given object can reduce storage spend by an order of magnitude without changing how the object is read or written by applications.

## S3 Standard

S3 Standard is the default storage class and is designed for frequently accessed data. It offers millisecond first-byte latency and high throughput, with data stored redundantly across a minimum of three Availability Zones. Standard is the right choice for active workloads such as content distribution, mobile and gaming applications, and big data analytics where objects are read often and unpredictably.

## S3 Intelligent-Tiering

S3 Intelligent-Tiering automatically moves objects between a frequent-access tier and infrequent-access tiers based on changing access patterns, without performance impact or operational overhead. The service monitors access patterns and, after 30 consecutive days without access, moves an object to the infrequent-access tier automatically; if the object is later accessed, it moves back to the frequent-access tier. Optional archive tiers can move objects that go unaccessed for 90 or 180 days into Glacier-class storage automatically. Intelligent-Tiering is ideal when access patterns are unknown or unpredictable, since there is no retrieval fee and no need to manually classify objects.

## S3 Standard-Infrequent Access and One Zone-IA

S3 Standard-IA is for data that is accessed less frequently but requires rapid access when needed, such as backups and disaster recovery files. It has the same durability and millisecond latency as Standard but a lower per-GB storage price and an added per-GB retrieval fee. S3 One Zone-IA stores data in a single Availability Zone rather than three, at an even lower price point, and is appropriate for reproducible data or secondary backup copies where losing the AZ would not be catastrophic.

## S3 Glacier storage classes

The S3 Glacier family (Glacier Instant Retrieval, Glacier Flexible Retrieval, and Glacier Deep Archive) is built for long-term archival at the lowest cost per GB. Glacier Instant Retrieval offers millisecond access for archive data accessed once a quarter, while Glacier Flexible Retrieval and Glacier Deep Archive trade retrieval speed (minutes to hours, or up to 12 hours for Deep Archive) for the lowest possible storage cost, making them suitable for compliance archives and data that may never be retrieved.

## Lifecycle policies

S3 Lifecycle configuration rules let objects transition automatically between storage classes, or expire entirely, based on the object's age. A common pattern is to keep objects in Standard for 30 days, transition to Standard-IA for 60 days, then to Glacier Flexible Retrieval, and finally expire the object after a compliance-driven retention period. Lifecycle rules apply per-prefix or per-tag, so different data types in the same bucket can follow different transition schedules.
