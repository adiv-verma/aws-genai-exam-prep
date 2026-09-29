"""
Code-first agent loop for the Task 2.1 ISP customer support system.

Bedrock Agents (classic) is in Maintenance Mode and closed to this account, so the
Reason -> Act -> Observe loop that a managed agent would run internally is written
out here instead. That turns out to be the more instructive version: every part the
managed service hides is visible and tunable.

Maps onto the Task 2.1 notes as follows:

  * Section 1.1 - the core agent loop. converse() returns either toolUse blocks
    (Act) or a final answer. Tool results are handed back as toolResult blocks
    (Observe) and the loop repeats (Reason).
  * Section 1.5 - the three-tier memory hierarchy. Operational memory rebuilds the
    conversation across invocations; tactical memory records what the agent did
    within one case so the reasoning is inspectable after the fact.
  * Section 2.2 - workflow-style CoT. Each tool call is persisted as it happens, so
    a failure on step 4 does not destroy the evidence from steps 1-3.
  * Section 4, layer 4 - stopping conditions. MAX_ITERATIONS bounds the loop; the
    model cannot spin indefinitely no matter what it decides to do.
"""

import json
import os
import time
from decimal import Decimal

import boto3

MODEL_ID = os.environ.get("MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
TOOLS_FUNCTION = os.environ.get("TOOLS_FUNCTION", "adi-2-1-support-tools")
SESSION_TABLE = os.environ.get("SESSION_TABLE", "adi-2-1-session-memory")
SCRATCHPAD_TABLE = os.environ.get("SCRATCHPAD_TABLE", "adi-2-1-decision-scratchpad")

# Section 4, layer 4: the loop is bounded here, not by the model's judgement.
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "6"))
# Section 1.5: operational memory is session-scoped and expires. 90 days per the notes.
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_DAYS", "90")) * 86400
# Tactical memory is a working scratchpad - it should not outlive the case by much.
SCRATCHPAD_TTL_SECONDS = int(os.environ.get("SCRATCHPAD_TTL_DAYS", "7")) * 86400
HISTORY_TURNS = int(os.environ.get("HISTORY_TURNS", "10"))

bedrock = boto3.client("bedrock-runtime")
lam = boto3.client("lambda")
ddb = boto3.resource("dynamodb")

SYSTEM_PROMPT = """You are a customer support agent for an internet service provider.

Establish the facts with your tools before offering advice. Work in this order:

1. getAccountStatus first, to identify the customer, their plan and their service area.
   If you do not have an account id, ask for it before calling anything.
2. For any connectivity or speed complaint, call getOutageStatus next, using the
   area_code that getAccountStatus returned. If an outage is active, give the cause and
   the restore time and stop. Do not ask the customer to reboot during a known outage.
3. If billing_status is past_due, say so plainly. Hardware troubleshooting will not fix
   a service throttled for non-payment.
4. Only once billing and outages are ruled out, call runLineDiagnostics. Judge the
   result against the customer's plan speed, not an absolute number. A modem_uptime_hours
   under 1 means the modem is rebooting repeatedly - that is power or hardware.

If a tool returns an error, read it. Use any valid alternatives it offers instead of
guessing. If it says the failure is fatal, stop and tell the customer you are escalating.

Never invent an outage, balance, speed or restore time. If you do not have a fact from a
tool, say you do not have it. Ask one question at a time. Keep answers short and plain."""

FACTS_HEADER = (
    "\n\nFacts already established by your tools earlier in this case. Treat these "
    "as authoritative and quote them exactly rather than calling the tool again. If "
    "the customer asks for something NOT listed here and not in the conversation, "
    "either call the tool for it or say you do not have it - never guess a "
    "plausible-looking value.\n"
)

TOOL_CONFIG = {
    "tools": [
        {"toolSpec": {
            "name": "getAccountStatus",
            "description": (
                "Look up a customer's plan, advertised speed, service area and billing "
                "state. Call this first: it returns the area_code that getOutageStatus "
                "needs, and the plan_speed_mbps that makes a diagnostic reading meaningful."
            ),
            "inputSchema": {"json": {
                "type": "object",
                "properties": {"account_id": {
                    "type": "string",
                    "description": "The customer's account identifier, for example ACC-1001."}},
                "required": ["account_id"]}}}},
        {"toolSpec": {
            "name": "getOutageStatus",
            "description": (
                "Check whether a known network outage is active in a service area. Call "
                "this before any hardware troubleshooting for a connectivity complaint. "
                "Use the area_code returned by getAccountStatus - the customer will not "
                "know it themselves."
            ),
            "inputSchema": {"json": {
                "type": "object",
                "properties": {"area_code": {
                    "type": "string",
                    "description": "Service area code, for example AREA-NORTH."}},
                "required": ["area_code"]}}}},
        {"toolSpec": {
            "name": "runLineDiagnostics",
            "description": (
                "Run a live diagnostic against the customer's physical line and modem. "
                "Only call this once a billing problem and an area-wide outage have both "
                "been ruled out. Returns sync speed, packet loss, modem uptime and signal."
            ),
            "inputSchema": {"json": {
                "type": "object",
                "properties": {"account_id": {
                    "type": "string",
                    "description": "The customer's account identifier, for example ACC-1001."}},
                "required": ["account_id"]}}}},
    ]
}

ROUTES = {
    "getAccountStatus": ("/account-status", "GET", "query"),
    "getOutageStatus": ("/outage-status", "GET", "query"),
    "runLineDiagnostics": ("/line-diagnostics", "POST", "body"),
}


# ---------------------------------------------------------------- memory tiers

def load_session_history(session_id):
    """Operational tier: rebuild the conversation from the last HISTORY_TURNS turns.

    One Query against the partition, newest first, bounded by Limit - no Scan and no
    filter expression, because turnTimestamp was chosen as the sort key precisely so
    this access pattern would be a single seek.
    """
    table = ddb.Table(SESSION_TABLE)
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("sessionId").eq(session_id),
        ScanIndexForward=False,
        Limit=HISTORY_TURNS,
    )
    turns = sorted(resp.get("Items", []), key=lambda i: i["turnTimestamp"])
    return [{"role": t["role"], "content": [{"text": t["text"]}]} for t in turns]


def save_turn(session_id, role, text, turn_ts):
    table = ddb.Table(SESSION_TABLE)
    table.put_item(Item={
        "sessionId": session_id,
        "turnTimestamp": Decimal(str(turn_ts)),
        "role": role,
        "text": text,
        "expiresAt": Decimal(str(int(time.time()) + SESSION_TTL_SECONDS)),
    })


def load_established_facts(case_id, limit=12):
    """Tactical tier, read path: the facts this case has already established.

    Bug 1 fix. Operational memory stores the *conversation*, which is only what the
    agent chose to say out loud. Facts a tool returned but the agent never mentioned
    - the customer's plan, their balance - vanish from context on the next turn, and
    the model will confabulate them rather than admit the gap. The tactical tier
    already has them; it just was not being read back.
    """
    table = ddb.Table(SCRATCHPAD_TABLE)
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("caseId").eq(case_id),
        ScanIndexForward=False,
        Limit=limit,
    )
    facts = []
    for item in sorted(resp.get("Items", []), key=lambda i: i["stepId"]):
        facts.append(f"- {item['tool']}({item['input']}) returned {item['output']}")
    return facts


def save_scratchpad_step(case_id, step_no, tool_name, tool_input, tool_output, iteration):
    """Tactical tier: persist each act/observe pair as it happens.

    Section 2.2 - this is what makes workflow CoT recoverable. If the loop dies on
    iteration 4, iterations 1-3 are already durable and do not need to be redone.
    """
    table = ddb.Table(SCRATCHPAD_TABLE)
    table.put_item(Item={
        "caseId": case_id,
        "stepId": f"{int(time.time()*1000)}#{step_no:02d}#{tool_name}",
        "iteration": iteration,
        "tool": tool_name,
        "input": json.dumps(tool_input),
        "output": json.dumps(tool_output)[:3000],
        "expiresAt": Decimal(str(int(time.time()) + SCRATCHPAD_TTL_SECONDS)),
    })


# ------------------------------------------------------------------ tool calls

def call_tool(name, args):
    route = ROUTES.get(name)
    if route is None:
        return {"error": f"Unknown tool {name}.", "error_class": "fatal"}
    api_path, method, style = route
    event = {"messageVersion": "1.0", "actionGroup": "support-tools",
             "apiPath": api_path, "httpMethod": method}
    if style == "query":
        event["parameters"] = [{"name": k, "type": "string", "value": str(v)}
                               for k, v in args.items()]
    else:
        event["requestBody"] = {"content": {"application/json": {"properties": [
            {"name": k, "type": "string", "value": str(v)} for k, v in args.items()]}}}

    resp = lam.invoke(FunctionName=TOOLS_FUNCTION, Payload=json.dumps(event).encode())
    payload = json.load(resp["Payload"])
    body = payload["response"]["responseBody"]["application/json"]["body"]
    return json.loads(body)


# ------------------------------------------------------------------- the loop

def lambda_handler(event, context):
    session_id = event.get("sessionId")
    user_input = event.get("userInput", "")
    case_id = event.get("caseId", session_id)

    if not session_id or not user_input:
        return {"statusCode": 400,
                "error": "sessionId and userInput are both required."}

    facts = load_established_facts(case_id)
    system_prompt = SYSTEM_PROMPT
    if facts:
        system_prompt += FACTS_HEADER + "\n".join(facts)

    messages = load_session_history(session_id)
    messages.append({"role": "user", "content": [{"text": user_input}]})

    turn_ts = time.time()
    save_turn(session_id, "user", user_input, turn_ts)

    trace = []
    totals = {"inputTokens": 0, "outputTokens": 0}
    step_no = 0
    stop_reason = "max_iterations"
    final_text = ""

    for iteration in range(1, MAX_ITERATIONS + 1):
        resp = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=[{"text": system_prompt}],
            toolConfig=TOOL_CONFIG,
            inferenceConfig={"maxTokens": 700, "temperature": 0.2},
        )
        usage = resp.get("usage", {})
        totals["inputTokens"] += usage.get("inputTokens", 0)
        totals["outputTokens"] += usage.get("outputTokens", 0)

        out = resp["output"]["message"]
        messages.append(out)

        tool_uses = [c["toolUse"] for c in out["content"] if "toolUse" in c]
        if not tool_uses:
            final_text = "".join(c.get("text", "") for c in out["content"])
            stop_reason = resp.get("stopReason", "end_turn")
            break

        tool_results = []
        for use in tool_uses:
            step_no += 1
            result = call_tool(use["name"], use["input"])
            save_scratchpad_step(case_id, step_no, use["name"], use["input"],
                                 result, iteration)
            trace.append({"iteration": iteration, "tool": use["name"],
                          "input": use["input"],
                          "error_class": result.get("error_class")})
            tool_results.append({"toolResult": {
                "toolUseId": use["toolUseId"],
                "content": [{"json": result}],
            }})
        messages.append({"role": "user", "content": tool_results})
    else:
        # Section 4, layer 4: the loop hit its ceiling. Degrade gracefully with the
        # work already done rather than looping forever or throwing it away.
        final_text = ("I have not been able to resolve this within my diagnostic "
                      "limit. I am handing this to a human technician with everything "
                      "I have checked so far.")

    save_turn(session_id, "assistant", final_text, time.time())

    return {
        "statusCode": 200,
        "sessionId": session_id,
        "caseId": case_id,
        "response": final_text,
        "stopReason": stop_reason,
        "iterations": len(set(t["iteration"] for t in trace)) or 1,
        "toolCalls": len(trace),
        "trace": trace,
        "usage": totals,
        "priorTurnsLoaded": len(messages) - len(trace) * 2 - 2,
        "factsLoaded": len(facts),
    }
