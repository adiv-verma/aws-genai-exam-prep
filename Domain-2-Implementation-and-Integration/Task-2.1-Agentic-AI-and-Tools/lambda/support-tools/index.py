"""
Action-group backend for the Task 2.1 ISP customer support agent.

Implements three read-only diagnostic tools behind the OpenAPI schema in
schemas/support-tools-openapi.json. The sample dataset is embedded rather than
read from S3 so the PoC has no cold-start dependency; the source of truth for
the data is data/isp-sample-data.json in this task folder.

Two ideas from the Task 2.1 notes are deliberately visible here:

  * Section 4, layer 2 - input validation. Parameters arrive from the *model*,
    not from a trusted caller, so every one is validated against business rules
    before it is used. The action group schema is not the security boundary.

  * Section 7 - model-readable errors. A failure returns the valid alternatives
    and an error_class the model can act on, rather than a bare 404. The agent
    is the consumer of these strings, so they are written for it to recover
    from, not for a human to read in a log.
"""

import json

DATA = {
    "accounts": {
        "ACC-1001": {
            "customer_name": "Priya Raman", "area_code": "AREA-NORTH",
            "plan": "Fibre 500 Mbps", "plan_speed_mbps": 500,
            "billing_status": "current", "balance_due_usd": 0.0,
            "modem_model": "TG-4482",
        },
        "ACC-1002": {
            "customer_name": "Daniel Okafor", "area_code": "AREA-SOUTH",
            "plan": "Cable 200 Mbps", "plan_speed_mbps": 200,
            "billing_status": "past_due", "balance_due_usd": 89.5,
            "modem_model": "CM-2100",
        },
        "ACC-1003": {
            "customer_name": "Mei Lin Chen", "area_code": "AREA-NORTH",
            "plan": "Fibre 1 Gbps", "plan_speed_mbps": 1000,
            "billing_status": "current", "balance_due_usd": 0.0,
            "modem_model": "TG-6600",
        },
    },
    "outages": {
        "AREA-NORTH": {
            "active": True, "incident_id": "INC-4471",
            "cause": "Fibre cut during municipal roadworks",
            "started_at": "2026-09-28T06:15:00Z",
            "estimated_restore_at": "2026-09-28T22:00:00Z",
            "customers_affected": 1840,
        },
        "AREA-SOUTH": {"active": False},
        "AREA-WEST": {
            "active": True, "incident_id": "INC-4468",
            "cause": "Scheduled node maintenance",
            "started_at": "2026-09-28T02:00:00Z",
            "estimated_restore_at": "2026-09-28T05:00:00Z",
            "customers_affected": 320,
        },
    },
    "line_diagnostics": {
        "ACC-1001": {"sync_speed_mbps": 12, "packet_loss_pct": 18.4,
                     "modem_uptime_hours": 0.4, "signal_dbm": -31, "verdict": "degraded"},
        "ACC-1002": {"sync_speed_mbps": 194, "packet_loss_pct": 0.2,
                     "modem_uptime_hours": 412.0, "signal_dbm": -8, "verdict": "healthy"},
        "ACC-1003": {"sync_speed_mbps": 940, "packet_loss_pct": 0.0,
                     "modem_uptime_hours": 1203.5, "signal_dbm": -6, "verdict": "healthy"},
    },
}


class ToolError(Exception):
    """A failure the model should be told about in a form it can act on."""

    def __init__(self, status, message, error_class, **extra):
        super().__init__(message)
        self.status = status
        self.payload = {"error": message, "error_class": error_class, **extra}


def _query_params(event):
    return {p["name"]: p["value"] for p in event.get("parameters", [])}


def _body_params(event):
    props = (
        event.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("properties", [])
    )
    return {p["name"]: p["value"] for p in props}


def _require_account(account_id):
    """Validate an account id coming from the model, not from a trusted caller."""
    if not account_id:
        raise ToolError(
            400,
            "account_id is required. Call getAccountStatus with the customer's "
            "account identifier, for example ACC-1001.",
            "fixable",
            valid_account_ids=sorted(DATA["accounts"]),
        )
    account_id = str(account_id).strip().upper()
    if account_id not in DATA["accounts"]:
        # Section 7: hand the model the valid alternatives so it can self-correct
        # on the next turn instead of apologising to the customer.
        raise ToolError(
            404,
            f"No account matches '{account_id}'. Ask the customer to confirm their "
            f"account number, or retry with one of the known identifiers.",
            "fixable",
            valid_account_ids=sorted(DATA["accounts"]),
        )
    return account_id


def get_account_status(event):
    account_id = _require_account(_query_params(event).get("account_id"))
    return {"account_id": account_id, **DATA["accounts"][account_id]}


def get_outage_status(event):
    area_code = _query_params(event).get("area_code")
    if not area_code:
        raise ToolError(
            400,
            "area_code is required. Call getAccountStatus first to obtain the "
            "customer's area_code; the customer will not know it themselves.",
            "fixable",
            valid_area_codes=sorted(DATA["outages"]),
        )
    area_code = str(area_code).strip().upper()
    if area_code not in DATA["outages"]:
        raise ToolError(
            404,
            f"No service area matches '{area_code}'. Use the area_code returned by "
            f"getAccountStatus verbatim.",
            "fixable",
            valid_area_codes=sorted(DATA["outages"]),
        )
    return {"area_code": area_code, **DATA["outages"][area_code]}


def run_line_diagnostics(event):
    params = _body_params(event) or _query_params(event)
    account_id = _require_account(params.get("account_id"))
    result = DATA["line_diagnostics"].get(account_id)
    if result is None:
        raise ToolError(
            503,
            "The diagnostic probe did not return a reading for this line. This is "
            "usually transient - retry once. If it fails again, escalate to a "
            "field technician rather than continuing to troubleshoot.",
            "retryable",
        )
    account = DATA["accounts"][account_id]
    # Speed is only meaningful relative to what the customer pays for.
    pct = round(100.0 * result["sync_speed_mbps"] / account["plan_speed_mbps"], 1)
    return {"account_id": account_id, "plan_speed_mbps": account["plan_speed_mbps"],
            "pct_of_plan_speed": pct, **result}


ROUTES = {
    ("/account-status", "GET"): get_account_status,
    ("/outage-status", "GET"): get_outage_status,
    ("/line-diagnostics", "POST"): run_line_diagnostics,
}


def lambda_handler(event, context):
    api_path = event.get("apiPath", "")
    http_method = event.get("httpMethod", "")
    handler = ROUTES.get((api_path, http_method))

    if handler is None:
        status, body = 404, {
            "error": f"No such operation: {http_method} {api_path}.",
            "error_class": "fatal",
            "available_operations": [f"{m} {p}" for p, m in ROUTES],
        }
    else:
        try:
            status, body = 200, handler(event)
        except ToolError as exc:
            status, body = exc.status, exc.payload
        except Exception as exc:  # never leak a stack trace back into the prompt
            print(f"unhandled error in {http_method} {api_path}: {exc!r}")
            status, body = 500, {
                "error": "The tool failed unexpectedly. Do not retry; tell the "
                         "customer you are escalating and stop troubleshooting.",
                "error_class": "fatal",
            }

    print(json.dumps({"apiPath": api_path, "httpMethod": http_method,
                      "httpStatusCode": status}))

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup"),
            "apiPath": api_path,
            "httpMethod": http_method,
            "httpStatusCode": status,
            "responseBody": {"application/json": {"body": json.dumps(body)}},
        },
        "sessionAttributes": event.get("sessionAttributes", {}),
        "promptSessionAttributes": event.get("promptSessionAttributes", {}),
    }
