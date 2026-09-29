"""
Safeguarded model invocation for Task 2.1 - notes Section 4, layers 3 and 5.

Wraps every Bedrock call in two independent protections:

  Timeout (layer 3)         - the call is given a hard deadline derived from the
                              Lambda's own remaining time, so it can never be the
                              thing that runs the function out of budget. On expiry
                              the partial state is saved and a fallback is returned.

  Circuit breaker (layer 5) - failures are counted in a sliding window. Past a
                              threshold the circuit OPENS and calls stop being
                              attempted at all, returning the fallback immediately.
                              After a cooldown one probe is allowed (HALF_OPEN); it
                              either closes the circuit or re-opens it.

Three corrections to the reference implementation in project.md Part 3:

 1. Its record_call_result() uses
        "SET calls = if_not_exists(calls, :empty_list) + :call"
    which is not valid DynamoDB. `+` is arithmetic only; list concatenation needs
    list_append(). Verified live: ValidationException, "Incorrect operand type for
    operator or function: +, operand type: L".

 2. It appends every call to an unbounded list on one item, then filters it in the
    client on every read. That item grows without limit toward the 400 KB cap, and
    the read cost grows with it. Counters with a rolling window are O(1) forever.

 3. It opens the circuit whenever error_rate > 0.5 with no minimum sample size, so a
    single failed call is a 100% error rate and trips the breaker for every user.
    MIN_CALLS makes the rate mean something before it is acted on.
"""

import json
import os
import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError, ConnectTimeoutError

TABLE = os.environ.get("CIRCUIT_BREAKER_TABLE", "adi-2-1-circuit-breaker")
MODEL_ID = os.environ.get("MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

FAILURE_THRESHOLD = float(os.environ.get("FAILURE_THRESHOLD", "0.5"))
MIN_CALLS = int(os.environ.get("MIN_CALLS", "5"))
WINDOW_SECONDS = int(os.environ.get("WINDOW_SECONDS", "300"))
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "60"))
RESERVE_MS = int(os.environ.get("RESERVE_MS", "3000"))

ddb = boto3.resource("dynamodb")
table = ddb.Table(TABLE)
cw = boto3.client("cloudwatch")
METRIC_NAMESPACE = "adi-2-1/Safeguards"


def emit(metric, service, value=1.0):
    """Publish a breaker transition so an alarm can act on it.

    The Lambda catches its own failures and returns 200 with a fallback, which is
    correct behaviour but means the built-in AWS/Lambda Errors metric stays flat -
    a degraded system would look perfectly healthy on the default dashboard. The
    breaker has to say so itself.
    """
    try:
        cw.put_metric_data(Namespace=METRIC_NAMESPACE, MetricData=[{
            "MetricName": metric,
            "Dimensions": [{"Name": "ServiceName", "Value": service}],
            "Value": value, "Unit": "Count"}])
    except Exception as exc:
        print(f"metric emit failed (non-fatal): {exc}")


# -------------------------------------------------------------- circuit state

def get_circuit(service):
    try:
        item = table.get_item(Key={"serviceName": service}).get("Item")
    except ClientError as exc:
        # If the breaker's own store is unreachable, fail OPEN-to-traffic (i.e.
        # allow the call). A broken breaker must not become the outage.
        print(f"circuit store unreadable, failing open: {exc}")
        return {"status": "CLOSED", "successCount": 0, "failureCount": 0,
                "windowStart": int(time.time()), "resetAt": 0}
    if not item:
        return {"status": "CLOSED", "successCount": 0, "failureCount": 0,
                "windowStart": int(time.time()), "resetAt": 0}
    return {
        "status": item.get("status", "CLOSED"),
        "successCount": int(item.get("successCount", 0)),
        "failureCount": int(item.get("failureCount", 0)),
        "windowStart": int(item.get("windowStart", time.time())),
        "resetAt": int(item.get("resetAt", 0)),
    }


def set_status(service, status, reset_at=0, clear_window=False):
    expr = "SET #s = :s, resetAt = :r, lastChanged = :t"
    vals = {":s": status, ":r": reset_at, ":t": int(time.time())}
    if clear_window:
        expr += ", successCount = :z, failureCount = :z, windowStart = :t"
        vals[":z"] = 0
    table.update_item(Key={"serviceName": service}, UpdateExpression=expr,
                      ExpressionAttributeNames={"#s": "status"},
                      ExpressionAttributeValues=vals)


def record(service, success, circuit):
    """O(1) counter update. Rolls the window rather than growing a list."""
    now = int(time.time())
    if now - circuit["windowStart"] > WINDOW_SECONDS:
        table.update_item(
            Key={"serviceName": service},
            UpdateExpression=("SET windowStart = :t, successCount = :s, failureCount = :f"),
            ExpressionAttributeValues={":t": now, ":s": 1 if success else 0,
                                       ":f": 0 if success else 1})
        return {"successCount": 1 if success else 0, "failureCount": 0 if success else 1}

    field = "successCount" if success else "failureCount"
    resp = table.update_item(
        Key={"serviceName": service},
        UpdateExpression=f"ADD {field} :one SET windowStart = if_not_exists(windowStart, :t)",
        ExpressionAttributeValues={":one": 1, ":t": now},
        ReturnValues="ALL_NEW")
    attrs = resp["Attributes"]
    return {"successCount": int(attrs.get("successCount", 0)),
            "failureCount": int(attrs.get("failureCount", 0))}


def fallback(reason, detail=""):
    return {
        "statusCode": 200,
        "servedBy": "fallback",
        "circuitReason": reason,
        "detail": detail,
        "body": ("Our AI assistant is temporarily unavailable. A support specialist "
                 "will pick this up shortly. If your service is down, you can check "
                 "for outages in your area from the status page in the meantime."),
    }


# --------------------------------------------------------------- the handler

def lambda_handler(event, context):
    service = event.get("serviceName", "bedrock-haiku")
    user_input = event.get("userInput", "")
    force_fail = bool(event.get("forceFail"))

    circuit = get_circuit(service)
    now = int(time.time())

    # OPEN: refuse without attempting, unless the cooldown has elapsed.
    if circuit["status"] == "OPEN":
        if now < circuit["resetAt"]:
            return {**fallback("circuit_open",
                               f"retry in {circuit['resetAt'] - now}s"),
                    "circuitStatus": "OPEN"}
        set_status(service, "HALF_OPEN", clear_window=True)
        circuit["status"] = "HALF_OPEN"

    # Layer 3: the model gets whatever time is left, minus a reserve to write state
    # and return cleanly. Derived from the real deadline, not a guessed constant.
    remaining_ms = context.get_remaining_time_in_millis() if context else 30000
    budget_s = max(2, (remaining_ms - RESERVE_MS) / 1000.0)

    bedrock = boto3.client("bedrock-runtime", config=Config(
        read_timeout=budget_s, connect_timeout=3, retries={"max_attempts": 0}))

    try:
        if force_fail:
            raise ClientError({"Error": {"Code": "ThrottlingException",
                                         "Message": "injected failure for testing"}},
                              "Converse")
        resp = bedrock.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": user_input}]}],
            inferenceConfig={"maxTokens": 300, "temperature": 0.2})
        text = "".join(c.get("text", "") for c in resp["output"]["message"]["content"])

        counts = record(service, True, circuit)
        if circuit["status"] == "HALF_OPEN":
            set_status(service, "CLOSED", clear_window=True)
            emit("CircuitClosed", service)
            print(f"circuit {service}: HALF_OPEN -> CLOSED (probe succeeded)")

        return {"statusCode": 200, "servedBy": "model", "body": text,
                "circuitStatus": "CLOSED", "budgetSeconds": round(budget_s, 1),
                "usage": resp.get("usage", {}), **counts}

    except (ReadTimeoutError, ConnectTimeoutError) as exc:
        counts = record(service, False, circuit)
        print(f"timeout after {budget_s:.1f}s: {exc}")
        return {**fallback("timeout", f"exceeded {budget_s:.1f}s budget"),
                "circuitStatus": circuit["status"], **counts}

    except Exception as exc:
        counts = record(service, False, circuit)
        total = counts["successCount"] + counts["failureCount"]
        rate = counts["failureCount"] / total if total else 0.0

        # A HALF_OPEN probe that fails re-opens immediately - no sample size needed,
        # the probe *was* the sample.
        if circuit["status"] == "HALF_OPEN" or (
                total >= MIN_CALLS and rate > FAILURE_THRESHOLD):
            set_status(service, "OPEN", reset_at=now + COOLDOWN_SECONDS)
            emit("CircuitOpened", service)
            print(f"circuit {service}: -> OPEN (rate {rate:.2f} over {total} calls)")
            return {**fallback("circuit_opened", f"error rate {rate:.0%} over {total} calls"),
                    "circuitStatus": "OPEN", "errorRate": round(rate, 2), **counts}

        print(f"call failed, circuit still CLOSED (rate {rate:.2f} over {total}): {exc}")
        return {**fallback("call_failed", str(exc)[:200]),
                "circuitStatus": "CLOSED", "errorRate": round(rate, 2), **counts}
