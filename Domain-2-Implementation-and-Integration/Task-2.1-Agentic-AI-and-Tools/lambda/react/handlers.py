"""
Step Functions ReAct workflow handlers for Task 2.1.

Five handlers, one deployment package, one Lambda function per handler. The state
machine owns the macro structure; each handler owns one micro decision. Notes §2.1
calls this the hybrid approach: macro-deterministic flow, micro-non-deterministic
reasoning.

  parse_request     - deterministic, no LLM   (§2.3 code-driven decomposition)
  determine_action  - LLM picks the next act  (Reason)
  action_handler    - executes one action     (Act)
  reasoning         - LLM evaluates results   (Observe -> Reason)
  generate_response - final customer answer

Every handler persists its own output to the tactical scratchpad before returning,
which is what makes this workflow CoT rather than prompt CoT: if the run dies at
step 4, steps 1-3 are already durable and inspectable (§2.2).
"""

import json
import os
import re
import time
from decimal import Decimal

import boto3

MODEL_ID = os.environ.get("MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
TOOLS_FUNCTION = os.environ.get("TOOLS_FUNCTION", "adi-2-1-support-tools")
SCRATCHPAD_TABLE = os.environ.get("SCRATCHPAD_TABLE", "adi-2-1-decision-scratchpad")
SCRATCHPAD_TTL_SECONDS = 7 * 86400

bedrock = boto3.client("bedrock-runtime")
lam = boto3.client("lambda")
ddb = boto3.resource("dynamodb")


def _record(case_id, step, payload):
    """Persist one reasoning step to the tactical tier as it happens (§2.2)."""
    ddb.Table(SCRATCHPAD_TABLE).put_item(Item={
        "caseId": case_id,
        "stepId": f"{int(time.time()*1000)}#wf#{step}",
        "tool": f"workflow:{step}",
        "input": "",
        "output": json.dumps(payload)[:3000],
        "expiresAt": Decimal(str(int(time.time()) + SCRATCHPAD_TTL_SECONDS)),
    })


def _ask(prompt, max_tokens=400):
    resp = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.0},
    )
    text = "".join(c.get("text", "") for c in resp["output"]["message"]["content"])
    return text, resp.get("usage", {})


def _json_from(text, fallback):
    """Models wrap JSON in prose or fences often enough to be worth handling."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return fallback
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return fallback


def _call_tool(name, args):
    routes = {"getAccountStatus": ("/account-status", "GET", "query"),
              "getOutageStatus": ("/outage-status", "GET", "query"),
              "runLineDiagnostics": ("/line-diagnostics", "POST", "body")}
    api_path, method, style = routes[name]
    event = {"messageVersion": "1.0", "actionGroup": "support-tools",
             "apiPath": api_path, "httpMethod": method}
    entries = [{"name": k, "type": "string", "value": str(v)} for k, v in args.items()]
    if style == "query":
        event["parameters"] = entries
    else:
        event["requestBody"] = {"content": {"application/json": {"properties": entries}}}
    resp = lam.invoke(FunctionName=TOOLS_FUNCTION, Payload=json.dumps(event).encode())
    body = json.load(resp["Payload"])["response"]["responseBody"]["application/json"]["body"]
    return json.loads(body)


# ------------------------------------------------------------------ 1. parse

ACCOUNT_RE = re.compile(r"\bACC-\d{4}\b", re.I)
INTENT_RULES = [
    ("billing", ("bill", "charge", "invoice", "payment", "refund", "overcharg", "past due")),
    ("connectivity", ("slow", "drop", "disconnect", "outage", "down", "crawl", "no internet",
                      "not working", "stopped working", "intermittent", "speed")),
    ("cancellation", ("cancel", "terminate", "close my account", "switch provider")),
]


def parse_request(event, context):
    """Deterministic decomposition - §2.3. No LLM call here, on purpose.

    A supplier delay (or here, a support ticket) must always trigger the same
    sub-checks. Letting a model decide how to split the problem risks it skipping a
    mandatory step on an off day. Regex runs in microseconds for a fraction of a cent
    and produces a structured contract the downstream steps can rely on.
    """
    case_id = event.get("caseId") or f"case-{int(time.time())}"
    text = event.get("userRequest", "")
    lowered = text.lower()

    account_match = ACCOUNT_RE.search(text)
    intent = "general"
    for name, keywords in INTENT_RULES:
        if any(k in lowered for k in keywords):
            intent = name
            break

    out = {
        "caseId": case_id,
        "userRequest": text,
        "intent": intent,
        "accountId": (account_match.group(0).upper() if account_match
                      else event.get("accountId")),
        "hasAccountId": bool(account_match or event.get("accountId")),
        "iteration": 0,
        "actionResults": [],
    }
    _record(case_id, "parse", {"intent": intent, "accountId": out["accountId"]})
    return out


# --------------------------------------------------------- 2. determine action

def determine_action(event, context):
    prompt = f"""You are the planner for an ISP support workflow. Choose the SINGLE next action.

Customer request: {event.get('userRequest')}
Detected intent: {event.get('intent')}
Account id known: {event.get('hasAccountId')}
Results gathered so far: {json.dumps(event.get('actionResults', []))[:1500]}

Available actions:
- "troubleshoot": gather account, outage and line-diagnostic facts for a connectivity problem.
- "billing": gather account and balance facts for a billing problem.
- "escalate": hand to a human. Use when the customer is asking to cancel, is threatening
  to leave, or when the gathered facts show a fault that needs a field technician.
- "none": enough facts have been gathered to answer; stop acting.

Reply with JSON only: {{"actionType": "...", "why": "one short sentence"}}"""

    text, usage = _ask(prompt, 200)
    decision = _json_from(text, {"actionType": "none", "why": "planner returned no parseable JSON"})
    if decision.get("actionType") not in ("troubleshoot", "billing", "escalate", "none"):
        decision["actionType"] = "none"

    _record(event["caseId"], f"determine-{event.get('iteration', 0)}", decision)
    return {**event, "actionType": decision["actionType"],
            "actionWhy": decision.get("why", ""), "plannerUsage": usage}


# ------------------------------------------------------------- 3. act

def action_handler(event, context):
    """Executes one action. The state machine routes three Choice branches here,
    each supplying a different `action` - so the graph still shows three distinct
    paths while the implementation stays in one place."""
    action = event.get("action") or event.get("actionType")
    account_id = event.get("accountId")
    results = list(event.get("actionResults", []))

    if action == "escalate":
        gathered = {"action": "escalate", "ticket": f"ESC-{int(time.time())}",
                    "note": "Handed to a human agent."}
    elif not account_id:
        gathered = {"action": action, "error": "No account id supplied.",
                    "error_class": "fixable",
                    "next": "Ask the customer for their account number."}
    elif action == "billing":
        account = _call_tool("getAccountStatus", {"account_id": account_id})
        gathered = {"action": "billing", "account": account}
    else:  # troubleshoot
        account = _call_tool("getAccountStatus", {"account_id": account_id})
        gathered = {"action": "troubleshoot", "account": account}
        if not account.get("error"):
            gathered["outage"] = _call_tool("getOutageStatus",
                                            {"area_code": account["area_code"]})
            if not gathered["outage"].get("active"):
                gathered["diagnostics"] = _call_tool("runLineDiagnostics",
                                                     {"account_id": account_id})

    results.append(gathered)
    _record(event["caseId"], f"act-{action}-{event.get('iteration', 0)}", gathered)
    return {**event, "actionResults": results}


# --------------------------------------------------------------- 4. reasoning

def reasoning(event, context):
    prompt = f"""You are the reasoning step of an ISP support workflow.

Customer request: {event.get('userRequest')}
Results gathered: {json.dumps(event.get('actionResults', []))[:2500]}

Answer these:
1. What is the customer's core issue?
2. Do the gathered facts explain it?
3. Is another action genuinely needed, or is there enough to answer now?

Be strict about question 3. An active outage, or a past-due balance, is a complete
explanation on its own - no further action is needed in those cases.

Reply with JSON only:
{{"coreIssue": "...", "explained": true/false, "needMoreActions": true/false,
  "confidence": 0.0-1.0, "reasoning": "two sentences"}}"""

    text, usage = _ask(prompt, 500)
    out = _json_from(text, {"coreIssue": "unknown", "explained": False,
                            "needMoreActions": False, "confidence": 0.3,
                            "reasoning": "reasoner returned no parseable JSON"})
    iteration = int(event.get("iteration", 0)) + 1
    payload = {**out, "iteration": iteration}
    _record(event["caseId"], f"reason-{iteration}", payload)
    return {**event, **payload, "needMoreActions": bool(out.get("needMoreActions")),
            "confidence": Decimal(str(out.get("confidence", 0.5))).__float__(),
            "reasonerUsage": usage}


# -------------------------------------------------------- 5. generate response

def generate_response(event, context):
    stopped_early = event.get("iteration", 0) >= int(os.environ.get("MAX_ITERATIONS", "3"))
    prompt = f"""Write the reply the ISP support agent sends to the customer.

Customer request: {event.get('userRequest')}
Facts gathered: {json.dumps(event.get('actionResults', []))[:2500]}
Internal reasoning: {event.get('reasoning', '')}

Rules: plain language, at most four sentences, no markdown. State only facts present
above - never invent an outage, balance, speed or restore time. If an outage is active,
give the cause and restore time and do not suggest rebooting. If the balance is past
due, say so plainly.{' Note: the workflow hit its action limit, so acknowledge that a human will follow up.' if stopped_early else ''}"""

    text, usage = _ask(prompt, 400)
    final = text.strip()
    _record(event["caseId"], "respond", {"response": final, "stoppedEarly": stopped_early})
    return {
        "caseId": event["caseId"],
        "response": final,
        "coreIssue": event.get("coreIssue"),
        "confidence": event.get("confidence"),
        "iterations": event.get("iteration", 0),
        "actionsTaken": [r.get("action") for r in event.get("actionResults", [])],
        "stoppedAtLimit": stopped_early,
        "responderUsage": usage,
    }
