import json
import os
import re
from datetime import datetime, timezone

import boto3

s3 = boto3.client("s3")
cloudwatch = boto3.client("cloudwatch")

QUALITY_THRESHOLD = float(os.environ.get("QUALITY_THRESHOLD", "0.7"))
REQUIRED_FIELDS = ("review_text", "product_id", "customer_id")


def handler(event, context):
    results = []
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if not key.endswith(".json"):
            continue

        response = s3.get_object(Bucket=bucket, Key=key)
        review = json.loads(response["Body"].read().decode("utf-8"))

        validation = validate_review(review)

        cloudwatch.put_metric_data(
            Namespace="CustomerFeedback/TextQuality",
            MetricData=[
                {
                    "MetricName": "QualityScore",
                    "Value": validation["quality_score"],
                    "Unit": "None",
                    "Dimensions": [{"Name": "Source", "Value": "TextReviews"}],
                },
                {
                    "MetricName": "ValidationPass",
                    "Value": 1.0 if validation["quality_score"] >= QUALITY_THRESHOLD else 0.0,
                    "Unit": "None",
                    "Dimensions": [{"Name": "Source", "Value": "TextReviews"}],
                },
            ],
        )

        validation_key = key.replace("raw-data/reviews", "validation-results/reviews").replace(
            ".json", "_validation.json"
        )
        s3.put_object(
            Bucket=bucket,
            Key=validation_key,
            Body=json.dumps(validation),
            ContentType="application/json",
        )
        results.append({"key": key, "quality_score": validation["quality_score"]})

    return {"statusCode": 200, "body": json.dumps(results)}


def validate_review(review):
    text = review.get("review_text", "") or ""
    checks = {
        "min_length": len(text) >= 10,
        "has_product_reference_or_context": bool(
            re.search(r"product|item|purchase|earbud|case|sound|battery|pair|charg", text, re.IGNORECASE)
        )
        or len(text) >= 40,
        "has_opinion": bool(
            re.search(
                r"like|love|hate|good|bad|great|terrible|excellent|poor|recommend|happy|disappoint",
                text,
                re.IGNORECASE,
            )
        ),
        "has_structure": text.count(".") >= 1 or text.count("!") >= 1,
        "required_fields_present": all(bool(review.get(f)) for f in REQUIRED_FIELDS),
        "rating_in_range": _rating_in_range(review.get("rating")),
        "date_format_valid": bool(re.match(r"^\d{4}-\d{2}-\d{2}$", str(review.get("review_date", "")))),
    }

    passed = sum(1 for v in checks.values() if v)
    quality_score = round(passed / len(checks), 4)

    return {
        "review_id": review.get("review_id", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "quality_score": quality_score,
        "is_valid": quality_score >= QUALITY_THRESHOLD,
    }


def _rating_in_range(rating):
    try:
        return 1 <= int(rating) <= 5
    except (TypeError, ValueError):
        return False
