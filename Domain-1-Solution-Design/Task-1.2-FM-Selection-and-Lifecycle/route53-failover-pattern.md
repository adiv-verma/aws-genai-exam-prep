# Route 53 failover pattern (documented, not deployed)

This task has two live, health-checked regional endpoints:

- **Primary (us-east-1):** `https://m4pnbttjnk.execute-api.us-east-1.amazonaws.com/prod/generate`
- **Secondary (us-west-2):** `https://bv4xaf9l6f.execute-api.us-west-2.amazonaws.com/prod/generate`

Each has a real Route 53 health check polling `GET /prod/health` every 30s (3 consecutive failures to mark unhealthy):

| Health Check | Region monitored | Health Check ID |
|---|---|---|
| `adi-1-2-primary-health-check` | us-east-1 | `35defb83-cdb0-4ace-8760-edb9f14378c9` |
| `adi-1-2-secondary-health-check` | us-west-2 | `d36d9429-f683-4766-8e66-285ffd09edf1` |

## Why no live DNS failover record set

Route 53 failover routing (`PRIMARY`/`SECONDARY` record sets with `EvaluateTargetHealth`) requires a **hosted zone for a domain you control**. This account has no registered domain, so there's nothing to point real `A`/alias records at without buying one. Per the user's decision (2026-09-15), this task stops at real health checks and documents the record set that *would* sit in front of them, rather than registering a domain just to complete this step.

## What the failover record set would look like

Assuming a hosted zone for `yourdomain.com` already existed, this is the exact CLI call that would wire up automatic regional failover for `ai-assistant.yourdomain.com` — a client would call this one hostname and Route 53 would silently route it to whichever region is healthy:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "ai-assistant.yourdomain.com",
          "Type": "A",
          "SetIdentifier": "Primary",
          "Failover": "PRIMARY",
          "AliasTarget": {
            "HostedZoneId": "Z1UJRXOUMOOFQ8",
            "DNSName": "m4pnbttjnk.execute-api.us-east-1.amazonaws.com",
            "EvaluateTargetHealth": true
          },
          "HealthCheckId": "35defb83-cdb0-4ace-8760-edb9f14378c9"
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "ai-assistant.yourdomain.com",
          "Type": "A",
          "SetIdentifier": "Secondary",
          "Failover": "SECONDARY",
          "AliasTarget": {
            "HostedZoneId": "Z2OJLYMUO9EFXC",
            "DNSName": "bv4xaf9l6f.execute-api.us-west-2.amazonaws.com",
            "EvaluateTargetHealth": true
          }
        }
      }
    ]
  }'
```

Notes on the values above:

- `HostedZoneId` inside each `AliasTarget` is **not** your own hosted zone ID — it's API Gateway's fixed per-region "alias target hosted zone ID" (`Z1UJRXOUMOOFQ8` for us-east-1, `Z2OJLYMUO9EFXC` for us-west-2 — these are constant, published by AWS for every API Gateway regional endpoint in that region, not account-specific).
- The **secondary** record doesn't need its own `HealthCheckId` — Route 53's failover logic only needs to know when the primary is down; if the primary health check fails, traffic automatically shifts to the secondary regardless of the secondary's own health (though in practice you'd usually health-check both, which is why both checks already exist above).
- `EvaluateTargetHealth: true` is what makes an *alias* record (as opposed to a plain CNAME) responsive to the linked health check's state in near-real time.

## What already deployed instead

Each regional API Gateway (`adi-1-2-api` in both us-east-1 and us-west-2) has a `GET /health` route (MOCK integration, no Lambda/Bedrock dependency, so it can't itself be a point of failure) purpose-built for exactly this: a Route 53 health check target that reflects "is this region's API reachable" without depending on downstream Bedrock/AppConfig health.
