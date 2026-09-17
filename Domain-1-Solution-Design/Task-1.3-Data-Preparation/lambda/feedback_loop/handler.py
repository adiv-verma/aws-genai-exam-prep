import base64
import json

import boto3

s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime")
cloudwatch = boto3.client("cloudwatch")

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
CONFIDENCE_THRESHOLD = 0.5

FEEDBACK_SYSTEM_PROMPT = (
    "You are assessing whether a piece of customer feedback contains enough "
    "concrete information to drive a business decision (e.g. escalate a defect, "
    "identify a specific complaint theme). Vague feedback with no specific detail "
    "should be marked low-confidence even if it is a well-formed, valid review. "
    "Respond with ONLY a JSON object: "
    '{"data_sufficient": true/false, "confidence": 0.0-1.0, "reasoning": "one sentence"}'
)


def handler(event, context):
    results = []
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if not key.startswith("formatted-data/reviews/") or not key.endswith("_formatted.json"):
            continue

        review_id = key.split("/")[-1].replace("_formatted.json", "")
        results.append(_process_review(bucket, key, review_id))

    return {"statusCode": 200, "body": json.dumps(results)}


def _process_review(bucket, formatted_key, review_id):
    formatted = json.loads(s3.get_object(Bucket=bucket, Key=formatted_key)["Body"].read())

    # Reuse the same user-turn content (the review text context) built in Step 9,
    # but with this Lambda's own structured-JSON system prompt.
    user_content = formatted["messages"][0]["content"]

    response = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": FEEDBACK_SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": user_content}],
        inferenceConfig={"maxTokens": 200, "temperature": 0},
    )
    raw_output = response["output"]["message"]["content"][0]["text"]
    assessment = _extract_json(raw_output)

    validation_key = f"validation-results/reviews/{review_id}_validation.json"
    validation = json.loads(s3.get_object(Bucket=bucket, Key=validation_key)["Body"].read())
    original_score = validation.get("quality_score", 1.0)

    confidence = assessment.get("confidence", 1.0)
    data_sufficient = assessment.get("data_sufficient", True)
    needs_adjustment = (not data_sufficient) or confidence < CONFIDENCE_THRESHOLD

    adjusted_score = round(original_score * confidence, 4) if needs_adjustment else original_score

    if needs_adjustment:
        validation["quality_score"] = adjusted_score
        validation["feedback_adjustment"] = {
            "original_quality_score": original_score,
            "adjusted_quality_score": adjusted_score,
            "bedrock_confidence": confidence,
            "data_sufficient": data_sufficient,
            "reasoning": assessment.get("reasoning", ""),
        }
        s3.put_object(
            Bucket=bucket,
            Key=validation_key,
            Body=json.dumps(validation),
            ContentType="application/json",
        )
        cloudwatch.put_metric_data(
            Namespace="CustomerFeedback/TextQuality",
            MetricData=[
                {
                    "MetricName": "FeedbackAdjustedQualityScore",
                    "Value": adjusted_score,
                    "Unit": "None",
                    "Dimensions": [{"Name": "Source", "Value": "TextReviews"}],
                }
            ],
        )

    audit_record = {
        "review_id": review_id,
        "bedrock_assessment": assessment,
        "original_quality_score": original_score,
        "adjusted_quality_score": adjusted_score,
        "adjustment_applied": needs_adjustment,
    }
    s3.put_object(
        Bucket=bucket,
        Key=f"quality-feedback/reviews/{review_id}_feedback.json",
        Body=json.dumps(audit_record),
        ContentType="application/json",
    )
    return audit_record


def _extract_json(text):
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])
