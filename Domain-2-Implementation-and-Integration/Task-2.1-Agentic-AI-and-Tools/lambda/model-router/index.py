"""
Model coordination and dynamic routing for Task 2.1 - notes Section 5.

A cheap model classifies the request; a routing table picks the model that fits;
a fallback chain covers failure. Three of the four coordination strategies in §5
are implemented here (ensembles are documented but not built - see progress.md).

  Task-based routing  - route by what the task needs, not by what is best overall.
  Dynamic selection   - the routing table is the starting point, then runtime
                        signals (remaining budget, an explicit latency requirement)
                        can downgrade the choice before the call is made.
  Fallback            - on failure, walk down the chain rather than returning an
                        error. A cheaper answer beats no answer.

Every decision is priced. Bedrock on-demand rates (us-east-1, USD per 1M tokens)
are pulled from the AWS Pricing API and pinned here so the router can report what
each choice actually cost rather than asserting that one is "cheaper".
"""

import json
import os
import time

import boto3
from botocore.exceptions import ClientError

bedrock = boto3.client("bedrock-runtime")

# us-east-1 on-demand, USD per 1M tokens. Verified via the AWS Pricing API
# (AmazonBedrockFoundationModels, USE1-MP:USE1_input_tokens_standard-Units).
MODELS = {
    "nova-micro": {
        "id": "amazon.nova-micro-v1:0",
        "in": 0.035, "out": 0.14, "api": "nova",
        "good_for": "classification, routing, short extraction",
    },
    "haiku": {
        "id": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
        "in": 1.10, "out": 5.50, "api": "anthropic",
        "good_for": "standard support reasoning, summarisation, tool use",
    },
    "sonnet": {
        "id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "in": 3.30, "out": 16.50, "api": "anthropic",
        "good_for": "multi-constraint reasoning, escalations, ambiguous complaints",
    },
}

# Task-based routing table (§5, strategy 1). Chosen by task shape, not by ranking.
ROUTING = {
    ("classification", "low"): "nova-micro",
    ("classification", "medium"): "nova-micro",
    ("classification", "high"): "haiku",
    ("qa", "low"): "haiku",
    ("qa", "medium"): "haiku",
    ("qa", "high"): "sonnet",
    ("generation", "low"): "haiku",
    ("generation", "medium"): "haiku",
    ("generation", "high"): "sonnet",
    ("reasoning", "low"): "haiku",
    ("reasoning", "medium"): "haiku",
    ("reasoning", "high"): "sonnet",
}
DEFAULT_MODEL = "haiku"

# Fallback chain (§5, strategy 4): each model's stand-in if it fails.
FALLBACK = {"sonnet": "haiku", "haiku": "nova-micro", "nova-micro": None}


def price(model_key, usage):
    m = MODELS[model_key]
    tin = usage.get("inputTokens", 0)
    tout = usage.get("outputTokens", 0)
    return round((tin * m["in"] + tout * m["out"]) / 1_000_000, 8)


def invoke(model_key, prompt, max_tokens=500, temperature=0.2, fail_models=()):
    """One call shape for both vendors. Converse normalises the request, but the
    usage keys and content shapes still differ enough to be worth isolating here."""
    if model_key in fail_models:
        # Test hook only: lets the fallback chain be exercised without waiting for a
        # real throttle. Never triggered unless simulateFailure is in the event.
        raise ClientError({"Error": {"Code": "ThrottlingException",
                                     "Message": "simulated for fallback test"}}, "Converse")
    m = MODELS[model_key]
    t0 = time.time()
    resp = bedrock.converse(
        modelId=m["id"],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    text = "".join(c.get("text", "") for c in resp["output"]["message"]["content"])
    usage = resp.get("usage", {})
    return {
        "text": text.strip(),
        "usage": usage,
        "costUsd": price(model_key, usage),
        "latencyMs": int((time.time() - t0) * 1000),
    }


def classify(user_input):
    """§5 strategy 1, the cheap half: a 30-token call on the cheapest model decides
    where the expensive call goes. At $0.035/$0.14 per MTok this costs about four
    millionths of a dollar - far less than the difference between routing right and
    routing wrong."""
    prompt = f"""Classify this ISP customer support request.

Request: {user_input}

taskType must be one of: classification, qa, generation, reasoning.
complexity must be one of: low, medium, high.
Use high only when the request has several competing constraints, an angry or
escalating customer, or a contradiction that needs unpicking.

Reply with JSON only: {{"taskType":"...","complexity":"...","why":"a few words"}}"""

    out = invoke("nova-micro", prompt, max_tokens=80, temperature=0.0)
    try:
        start = out["text"].index("{")
        parsed = json.loads(out["text"][start:out["text"].rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        parsed = {"taskType": "reasoning", "complexity": "medium",
                  "why": "classifier output unparseable, defaulted"}
    return parsed, out


def lambda_handler(event, context):
    user_input = event.get("userInput", "")
    if not user_input:
        return {"statusCode": 400, "error": "userInput is required."}

    fail_models = tuple(event.get("simulateFailure", []))
    budget_usd = event.get("maxCostUsd")          # dynamic selection signal
    require_fast = bool(event.get("requireFast"))  # dynamic selection signal

    classification, classifier_call = classify(user_input)
    task_type = classification.get("taskType", "reasoning")
    complexity = classification.get("complexity", "medium")

    chosen = ROUTING.get((task_type, complexity), DEFAULT_MODEL)
    route_reason = f"table[{task_type}/{complexity}]"
    downgrades = []

    # §5 strategy 2 - dynamic selection. The table is the default; runtime signals
    # can override it before any expensive call is made.
    if require_fast and chosen == "sonnet":
        downgrades.append("requireFast: sonnet -> haiku")
        chosen, route_reason = "haiku", "latency requirement"

    if budget_usd is not None:
        # Estimate this call against the remaining budget before committing to it.
        est_in = len(user_input) / 4 + 200
        estimate = (est_in * MODELS[chosen]["in"] + 400 * MODELS[chosen]["out"]) / 1_000_000
        while estimate > float(budget_usd) and FALLBACK[chosen]:
            cheaper = FALLBACK[chosen]
            downgrades.append(f"budget ${budget_usd}: {chosen} -> {cheaper} "
                              f"(est ${estimate:.6f})")
            chosen = cheaper
            estimate = (est_in * MODELS[chosen]["in"] + 400 * MODELS[chosen]["out"]) / 1_000_000
            route_reason = "budget constraint"

    answer_prompt = f"""You are an ISP customer support agent. Reply to this customer.

Request: {user_input}

Plain language, at most four sentences, no markdown. Do not invent account details,
outages, balances or speeds - if you need a fact you do not have, say so and offer to
look it up."""

    attempts = []
    model_key = chosen
    result = None
    while model_key:
        try:
            result = invoke(model_key, answer_prompt, fail_models=fail_models)
            attempts.append({"model": model_key, "ok": True})
            break
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            attempts.append({"model": model_key, "ok": False, "error": code})
            print(f"{model_key} failed ({code}), falling back to {FALLBACK[model_key]}")
            model_key = FALLBACK[model_key]

    if result is None:
        return {"statusCode": 503, "error": "Every model in the fallback chain failed.",
                "attempts": attempts}

    total = round(classifier_call["costUsd"] + result["costUsd"], 8)
    # What the same answer would have cost on the most capable model, for comparison.
    sonnet_equiv = price("sonnet", result["usage"])

    return {
        "statusCode": 200,
        "response": result["text"],
        "classification": classification,
        "routedTo": model_key,
        "routeReason": route_reason,
        "downgrades": downgrades,
        "fallbackUsed": model_key != chosen,
        "attempts": attempts,
        "cost": {
            "classifierUsd": classifier_call["costUsd"],
            "answerUsd": result["costUsd"],
            "totalUsd": total,
            "sonnetEquivalentUsd": sonnet_equiv,
            "savedVsSonnetUsd": round(sonnet_equiv - result["costUsd"], 8),
        },
        "latency": {"classifierMs": classifier_call["latencyMs"],
                    "answerMs": result["latencyMs"]},
        "usage": result["usage"],
    }
