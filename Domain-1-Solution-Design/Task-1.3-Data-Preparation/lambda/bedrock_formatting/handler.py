import base64
import json
import os

import boto3

s3 = boto3.client("s3")

SYSTEM_PROMPT = (
    "You are a customer insights analyst for TechSound, a consumer electronics brand. "
    "You are given one piece of processed customer feedback about the wireless earbuds "
    "product line (WEB-100 / WEB-200-PRO). Identify: (1) the core issue or praise, "
    "(2) whether this needs escalation (defect, safety, or fraud risk vs. routine feedback), "
    "(3) a one-sentence actionable recommendation for the product team. Be concise."
)


def handler(event, context):
    results = []
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if key.endswith("survey_summaries.json"):
            results.extend(_format_surveys(bucket, key))
        elif key.endswith("_processed.json"):
            results.append(_format_single(bucket, key))

    return {"statusCode": 200, "body": json.dumps(results)}


def _write_formatted(bucket, formatted_key, payload):
    s3.put_object(
        Bucket=bucket,
        Key=formatted_key,
        Body=json.dumps(payload),
        ContentType="application/json",
    )
    return formatted_key


def _format_single(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    data = json.loads(response["Body"].read().decode("utf-8"))

    if "transcript" in data:
        record_id, content_blocks = _format_audio(data)
        modality = "audio"
    elif "extracted_text" in data:
        record_id, content_blocks = _format_image(bucket, data)
        modality = "images"
    elif "entities" in data:
        record_id, content_blocks = _format_review(data)
        modality = "reviews"
    else:
        record_id, content_blocks = data.get("review_id", "unknown"), [{"text": json.dumps(data)}]
        modality = "other"

    payload = {
        "modelId": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "system": [{"text": SYSTEM_PROMPT}],
        "messages": [{"role": "user", "content": content_blocks}],
    }
    formatted_key = f"formatted-data/{modality}/{record_id}_formatted.json"
    return _write_formatted(bucket, formatted_key, payload)


def _format_review(data):
    text = (
        f"Source: customer text review\n"
        f"Product: {data['metadata'].get('product_id')}\n"
        f"Rating: {data['metadata'].get('rating')}/5\n"
        f"Sentiment: {data.get('sentiment')} (scores: {json.dumps(data.get('sentiment_scores', {}))})\n"
        f"Key phrases: {', '.join(data.get('key_phrases', []))}\n"
        f"Review text: \"{data.get('original_text', '')}\""
    )
    return data.get("review_id", "unknown"), [{"text": text}]


def _format_audio(data):
    text = (
        f"Source: customer service call transcript\n"
        f"Sentiment: {data.get('sentiment')} (scores: {json.dumps(data.get('sentiment_scores', {}))})\n"
        f"Key phrases: {', '.join(data.get('key_phrases', []))}\n"
        f"Transcript: \"{data.get('transcript', '')}\""
    )
    record_id = data.get("metadata", {}).get("call_id", "unknown")
    return record_id, [{"text": text}]


def _format_image(bucket, data):
    image_key = data["image_key"]
    ext = os.path.splitext(image_key)[1].lstrip(".").lower()
    img_format = "jpeg" if ext in ("jpg", "jpeg") else ext

    img_response = s3.get_object(Bucket=bucket, Key=image_key)
    image_bytes = img_response["Body"].read()

    labels = ", ".join(f"{l['name']} ({l['confidence']}%)" for l in data.get("labels", []))
    text = (
        f"Source: product image ({image_key})\n"
        f"Product: {data.get('metadata', {}).get('product_id')}\n"
        f"Text detected in image (Textract): \"{data.get('extracted_text', '')}\"\n"
        f"Visual labels detected (Rekognition): {labels}\n"
        f"Analyze both the image itself and the detected text/labels above."
    )
    # Bytes aren't JSON-serializable, so store base64 here; the Bedrock invoke
    # step (Step 10) decodes this back to raw bytes before calling Converse -
    # boto3's Converse API wants actual bytes, not a base64 string, in the
    # image content block.
    content_blocks = [
        {"text": text},
        {
            "image": {
                "format": img_format,
                "source": {"bytes_base64": base64.b64encode(image_bytes).decode("utf-8")},
            }
        },
    ]
    record_id = os.path.splitext(os.path.basename(image_key))[0]
    return record_id, content_blocks


def _format_surveys(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    summaries = json.loads(response["Body"].read().decode("utf-8"))
    formatted_keys = []
    for row in summaries:
        text = (
            f"Source: post-purchase satisfaction survey\n"
            f"Overall satisfaction: {row['ratings']['overall_satisfaction']}/5, "
            f"Product: {row['ratings']['product_rating']}/5, "
            f"Service: {row['ratings']['service_rating']}/5\n"
            f"Improvement area suggested: {row.get('improvement_area')}\n"
            f"Summary: {row.get('summary_text')}"
        )
        payload = {
            "modelId": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
            "system": [{"text": SYSTEM_PROMPT}],
            "messages": [{"role": "user", "content": [{"text": text}]}],
        }
        formatted_key = f"formatted-data/surveys/{row['customer_id']}_formatted.json"
        formatted_keys.append(_write_formatted(bucket, formatted_key, payload))
    return formatted_keys
