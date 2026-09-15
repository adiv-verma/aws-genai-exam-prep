import json

RESPONSES = {
    "product_question": (
        "I'm sorry, I'm unable to look up product details right now due to a "
        "temporary service issue. For immediate help with accounts, cards, or "
        "loans, please call us at 1-800-555-0199 or visit your nearest branch."
    ),
    "general": (
        "I'm sorry, but I'm currently experiencing technical difficulties. "
        "Please try again in a few minutes, or contact customer service at "
        "1-800-555-0199 for immediate assistance."
    ),
}

DEFAULT_RESPONSE = RESPONSES["general"]


def lambda_handler(event, context):
    """Final circuit-breaker stage: both the primary and fallback model calls
    failed, so return a safe, predefined response instead of an error - no
    Bedrock call, nothing that can itself fail."""
    use_case = event.get("use_case", "product_question")
    response_text = RESPONSES.get(use_case, DEFAULT_RESPONSE)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "model_used": "DEGRADED_SERVICE",
            "response": response_text,
        }),
    }
