import base64
import json

import boto3

BUCKET = "adi-1-3-customer-feedback-269737522732"
TEST_KEYS = [
    "formatted-data/reviews/rev-004_formatted.json",
    "formatted-data/images/WEB-100_case_damage_formatted.json",
    "formatted-data/audio/adi-1-3-call-002_defective_product-e0b3a379_formatted.json",
    "formatted-data/surveys/cust-2004_formatted.json",
]

session = boto3.Session(profile_name="awsgenai", region_name="us-east-1")
s3 = session.client("s3")
bedrock = session.client("bedrock-runtime")

for key in TEST_KEYS:
    print(f"\n{'=' * 80}\n{key}\n{'=' * 80}")
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    payload = json.loads(obj["Body"].read().decode("utf-8"))

    # Decode base64 image blocks back to raw bytes for the real Converse call.
    for msg in payload["messages"]:
        for block in msg["content"]:
            if "image" in block:
                b64 = block["image"]["source"].pop("bytes_base64")
                block["image"]["source"]["bytes"] = base64.b64decode(b64)

    response = bedrock.converse(
        modelId=payload["modelId"],
        system=payload["system"],
        messages=payload["messages"],
        inferenceConfig={"maxTokens": 300, "temperature": 0.2},
    )
    output_text = response["output"]["message"]["content"][0]["text"]
    usage = response["usage"]
    print(output_text)
    print(f"\n[tokens: {usage['inputTokens']} in / {usage['outputTokens']} out]")
