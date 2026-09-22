import json
import time

import boto3

bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

MODELS = [
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "us.anthropic.claude-sonnet-4-6",
]


def compare_models(prompt, models=MODELS, max_tokens=300):
    results = {}
    for model_id in models:
        start = time.time()
        response = bedrock_runtime.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.4, "maxTokens": max_tokens},
        )
        elapsed = time.time() - start
        text = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})
        results[model_id] = {
            "time_seconds": round(elapsed, 2),
            "output_length_chars": len(text),
            "input_tokens": usage.get("inputTokens"),
            "output_tokens": usage.get("outputTokens"),
            "output_text": text,
        }
    return results


if __name__ == "__main__":
    s3 = boto3.client("s3")
    bucket = "adi-1-1-claims-documents-269737522732"
    extracted = json.loads(s3.get_object(Bucket=bucket, Key="processed/claim2_property.json")["Body"].read())
    policy_excerpt = s3.get_object(Bucket=bucket, Key="policies/POL-HOME-55021.txt")["Body"].read().decode()

    prompt = f"""Based on this extracted claim information and the relevant policy excerpt,
write a concise 2-3 sentence claim summary suitable for an adjuster's queue. Mention
whether the claim amount appears to fall within the policy's relevant coverage limit.

Extracted claim info:
{json.dumps(extracted['extracted_info'], indent=2)}

Relevant policy excerpt:
{policy_excerpt}"""

    results = compare_models(prompt)
    print(json.dumps(results, indent=2))
