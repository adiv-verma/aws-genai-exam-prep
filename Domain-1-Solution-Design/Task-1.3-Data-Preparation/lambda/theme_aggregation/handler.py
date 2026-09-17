import json
from collections import Counter

import boto3

s3 = boto3.client("s3")

BUCKET = "adi-1-3-customer-feedback-269737522732"
PREFIX = "processed-data/reviews/"
OUTPUT_KEY = "insights/reviews_theme_summary.json"


def handler(event, context):
    paginator = s3.get_paginator("list_objects_v2")
    review_keys = [
        obj["Key"]
        for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX)
        for obj in page.get("Contents", [])
    ]

    entity_counter = Counter()
    entity_type_counter = Counter()
    key_phrase_counter = Counter()
    sentiment_counter = Counter()
    product_sentiment = {}

    for key in review_keys:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        review = json.loads(obj["Body"].read().decode("utf-8"))

        sentiment_counter[review.get("sentiment", "UNKNOWN")] += 1

        product_id = review.get("metadata", {}).get("product_id", "unknown")
        product_sentiment.setdefault(product_id, Counter())[review.get("sentiment", "UNKNOWN")] += 1

        for entity in review.get("entities", []):
            entity_counter[entity["Text"].lower()] += 1
            entity_type_counter[entity["Type"]] += 1

        for phrase in review.get("key_phrases", []):
            key_phrase_counter[phrase.lower()] += 1

    summary = {
        "total_reviews_analyzed": len(review_keys),
        "sentiment_distribution": dict(sentiment_counter),
        "sentiment_by_product": {
            product: dict(counts) for product, counts in product_sentiment.items()
        },
        "top_recurring_themes": [
            {"phrase": phrase, "count": count}
            for phrase, count in key_phrase_counter.most_common(10)
        ],
        "top_entities_mentioned": [
            {"entity": entity, "count": count} for entity, count in entity_counter.most_common(10)
        ],
        "entity_type_distribution": dict(entity_type_counter),
    }

    s3.put_object(
        Bucket=BUCKET,
        Key=OUTPUT_KEY,
        Body=json.dumps(summary, indent=2),
        ContentType="application/json",
    )

    return {"statusCode": 200, "body": json.dumps(summary)}
