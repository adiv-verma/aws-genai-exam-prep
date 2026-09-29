"""
Human-in-the-loop handlers for Task 2.1 - notes Section 6.

The escalation bands from §6 drive the routing:

    confidence > 0.9          fully automated
    0.7 <= confidence <= 0.9  automated, with asynchronous human review
    confidence < 0.7          synchronous human approval before anything is sent

High-sensitivity actions (cancellations, refunds, credits, legal threats) skip the
bands entirely and always gate, however confident the model is. Confidence measures
how sure the model is, not how much the mistake would cost.

The pause is implemented with a Step Functions **task token**, not a polling loop.
project.md Part 5 uses Wait -> CheckStatus -> Choice -> Wait, which bills a state
transition per poll, adds latency equal to half the poll interval, and needs the
reviewer's answer to be stored somewhere the poller can find it anyway. A token
inverts it: the execution parks at zero cost until someone calls SendTaskSuccess.
"""

import json
import os
import re
import time
import uuid
from decimal import Decimal

import boto3

REVIEW_TABLE = os.environ.get("REVIEW_TABLE", "adi-2-1-human-reviews")
MODEL_ID = os.environ.get("MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

AUTO_APPROVE_ABOVE = float(os.environ.get("AUTO_APPROVE_ABOVE", "0.9"))
SYNC_REVIEW_BELOW = float(os.environ.get("SYNC_REVIEW_BELOW", "0.7"))

# Bug 4: these were matched with `term in text`, so "sue" fired on "issue",
# "pursue" and "tissue" - flagging a large share of ordinary support traffic as
# HIGH sensitivity. Matched on word boundaries now. Stems that are meant to be
# prefixes (compensat-, cancel-) keep a trailing \w* so "compensation" and
# "cancellation" still match.
SENSITIVE_PATTERNS = re.compile(
    r"\b(cancel\w*|refund\w*|credit(?!\s+(?:card|score))\w*|compensat\w*|legal|lawyer|sue|suing|"
    r"ombudsman|terminat\w*|waive\w*|small claims)\b", re.I)

ddb = boto3.resource("dynamodb")
bedrock = boto3.client("bedrock-runtime")
sfn = boto3.client("stepfunctions")
table = ddb.Table(REVIEW_TABLE)


def _ask(prompt, max_tokens=400):
    resp = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.0})
    return "".join(c.get("text", "") for c in resp["output"]["message"]["content"])


def _json_from(text, fallback):
    try:
        return json.loads(text[text.index("{"):text.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        return fallback


# ------------------------------------------------- 1. draft + score confidence

def evaluate_confidence(event, context):
    """Produces the draft reply AND a self-assessed confidence, then applies the
    §6 bands plus the sensitivity override."""
    request = event.get("userRequest", "")
    facts = event.get("facts")

    # A confidence gate in front of a model with no tools sends nearly everything to
    # a human, because the model is correctly unsure about facts it cannot look up.
    # In the real pipeline this state runs AFTER the ReAct workflow has gathered
    # facts; `facts` is how they arrive.
    facts_block = (f"\nVerified facts already retrieved for this customer:\n"
                   f"{json.dumps(facts)}\n" if facts else
                   "\nNo facts have been retrieved. You have no tools here - if answering "
                   "correctly needs a lookup you have not been given, your confidence "
                   "should be low.\n")

    drafted = _ask(f"""You are an ISP support agent. Draft a reply to this customer, then
rate your own confidence in it.

Customer request: {request}
{facts_block}
confidence is 0.0-1.0: how certain are you that this reply is correct and complete
given only what the customer told you? Lower it when you are missing facts you would
normally look up, when the request is ambiguous, or when you are guessing.

decisionType must be one of: outage_info, billing_dispute, cancellation,
credit_or_refund, technical_troubleshooting, general_enquiry.

Reply with JSON only:
{{"draft":"the reply, max 4 sentences, no markdown","confidence":0.0,
  "decisionType":"...","why":"one sentence on the confidence score"}}""", 700)

    out = _json_from(drafted, {"draft": "I will need to check that and come back to you.",
                               "confidence": 0.3, "decisionType": "general_enquiry",
                               "why": "model output unparseable"})

    confidence = float(out.get("confidence", 0.5))
    decision_type = out.get("decisionType", "general_enquiry")

    matched = sorted(set(m.group(0).lower() for m in SENSITIVE_PATTERNS.finditer(request)))
    sensitive = bool(matched) or decision_type in ("cancellation", "credit_or_refund")

    if sensitive:
        trigger = f"terms {matched}" if matched else f"decisionType {decision_type}"
        route, why = "SYNC_REVIEW", f"sensitive action ({trigger}) - gated regardless of confidence"
    elif confidence > AUTO_APPROVE_ABOVE:
        route, why = "AUTO", f"confidence {confidence} > {AUTO_APPROVE_ABOVE}"
    elif confidence < SYNC_REVIEW_BELOW:
        route, why = "SYNC_REVIEW", f"confidence {confidence} < {SYNC_REVIEW_BELOW}"
    else:
        route, why = "ASYNC_REVIEW", f"confidence {confidence} in review band"

    return {
        "caseId": event.get("caseId", f"case-{int(time.time())}"),
        "userRequest": request,
        "draft": out.get("draft", ""),
        "confidence": Decimal(str(confidence)).__float__(),
        "decisionType": decision_type,
        "sensitivity": "HIGH" if sensitive else "NORMAL",
        "route": route,
        "sensitiveTerms": matched,
        "routeWhy": why,
        "modelWhy": out.get("why", ""),
    }


# ------------------------------------------------------- 2. park for a human

def create_review_task(event, context):
    """Writes the pending review WITH the task token. The token is the only way to
    resume the execution, so this write is the handoff - if it fails, the Catch in
    the state machine must clean up rather than leave the execution parked forever."""
    review_id = f"rev-{uuid.uuid4().hex[:12]}"
    now = int(time.time())
    table.put_item(Item={
        "reviewId": review_id,
        "caseId": event["caseId"],
        "decisionType": event["decisionType"],
        "reviewerId": "UNASSIGNED",
        "createdAt": now,
        "status": "PENDING",
        "confidence": Decimal(str(event["confidence"])),
        "sensitivity": event["sensitivity"],
        "routeWhy": event["routeWhy"],
        "userRequest": event["userRequest"],
        "proposedResponse": event["draft"],
        "taskToken": event["taskToken"],
    })
    print(json.dumps({"reviewId": review_id, "status": "PENDING",
                      "decisionType": event["decisionType"],
                      "confidence": event["confidence"]}))
    # Nothing is returned to the state machine here - the execution is now parked
    # and will only continue when SendTaskSuccess is called with this token.
    return {"reviewId": review_id}


# --------------------------------------------- 3. record the human's decision

def process_feedback(event, context):
    """Runs after the token resumes the execution. Stores the correction so the
    rejection patterns in §6 become queryable through the GSIs."""
    review_id = event.get("reviewId")
    verdict = event.get("verdict", "APPROVED")
    reviewer = event.get("reviewerId", "unknown")
    corrected = event.get("correctedResponse")

    final = corrected if (verdict == "REJECTED" and corrected) else event.get("draft", "")

    if review_id:
        table.update_item(
            Key={"reviewId": review_id},
            UpdateExpression=("SET #s = :s, reviewerId = :r, reviewedAt = :t, "
                              "finalResponse = :f, correctedResponse = :c "
                              "REMOVE taskToken"),
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": verdict, ":r": reviewer,
                                       ":t": int(time.time()), ":f": final,
                                       ":c": corrected or ""})

    return {**event, "verdict": verdict, "reviewerId": reviewer, "finalResponse": final}


# --------------------------------------------------------- 4. deliver / audit

def deliver_response(event, context):
    return {
        "caseId": event.get("caseId"),
        "reviewId": event.get("reviewId"),
        "decisionType": event.get("decisionType"),
        "confidence": event.get("confidence"),
        "sensitivity": event.get("sensitivity"),
        "route": event.get("route"),
        "routeWhy": event.get("routeWhy"),
        "verdict": event.get("verdict", "AUTO_APPROVED"),
        "reviewerId": event.get("reviewerId"),
        "response": event.get("finalResponse") or event.get("draft", ""),
        "deliveredAt": int(time.time()),
    }


# ------------------------------------- 5. timeout path (24h fallback from §6)

def handle_timeout(event, context):
    """§6: the wait has a 24-hour timeout fallback. Timing out must not silently
    send an unreviewed reply - it escalates to a human queue instead."""
    review_id = event.get("reviewId")
    if review_id:
        table.update_item(
            Key={"reviewId": review_id},
            UpdateExpression="SET #s = :s, reviewedAt = :t REMOVE taskToken",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "TIMED_OUT", ":t": int(time.time())})
    return {**event, "verdict": "TIMED_OUT", "reviewerId": "none",
            "finalResponse": ("We are looking into your request and a support "
                              "specialist will contact you directly.")}
