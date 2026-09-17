import html
import json
import re

import boto3

s3 = boto3.client("s3")
comprehend = boto3.client("comprehend")

QUALITY_THRESHOLD = 0.7

# Domain-specific shorthand seen in earbuds reviews/support text - expanded so
# Comprehend (and later Bedrock) sees full words instead of noisy shorthand.
ABBREVIATIONS = {
    r"\bw/(?=\s|$)": "with",
    r"\bBT\b": "Bluetooth",
    r"\bmins?\b": "minutes",
    r"\bapprox\b": "approximately",
}


def normalize_text(text):
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)  # strip HTML tags
    for pattern, replacement in ABBREVIATIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()  # collapse whitespace
    return text


def handler(event, context):
    results = []
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if not key.endswith("_validation.json"):
            continue

        response = s3.get_object(Bucket=bucket, Key=key)
        validation = json.loads(response["Body"].read().decode("utf-8"))

        if validation.get("quality_score", 0) < QUALITY_THRESHOLD:
            results.append({"key": key, "skipped": True, "reason": "quality_score below threshold"})
            continue

        original_key = key.replace("validation-results/reviews", "raw-data/reviews").replace(
            "_validation.json", ".json"
        )
        response = s3.get_object(Bucket=bucket, Key=original_key)
        review = json.loads(response["Body"].read().decode("utf-8"))
        raw_text = review.get("review_text", "")
        text = normalize_text(raw_text)

        entities = comprehend.detect_entities(Text=text, LanguageCode="en")
        sentiment = comprehend.detect_sentiment(Text=text, LanguageCode="en")
        key_phrases = comprehend.detect_key_phrases(Text=text, LanguageCode="en")

        processed_review = {
            "review_id": review.get("review_id"),
            "original_text": raw_text,
            "normalized_text": text,
            "entities": entities["Entities"],
            "sentiment": sentiment["Sentiment"],
            "sentiment_scores": sentiment["SentimentScore"],
            "key_phrases": [kp["Text"] for kp in key_phrases["KeyPhrases"]],
            "metadata": {
                "product_id": review.get("product_id", ""),
                "customer_id": review.get("customer_id", ""),
                "review_date": review.get("review_date", ""),
                "rating": review.get("rating", ""),
            },
        }

        processed_key = original_key.replace("raw-data/reviews", "processed-data/reviews").replace(
            ".json", "_processed.json"
        )
        s3.put_object(
            Bucket=bucket,
            Key=processed_key,
            Body=json.dumps(processed_review),
            ContentType="application/json",
        )
        results.append({"key": processed_key, "sentiment": sentiment["Sentiment"]})

    return {"statusCode": 200, "body": json.dumps(results)}
