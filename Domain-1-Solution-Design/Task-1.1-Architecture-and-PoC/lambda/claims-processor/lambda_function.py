import json
import os
import re
import urllib.parse

import boto3

s3 = boto3.client("s3")
bedrock_runtime = boto3.client("bedrock-runtime")

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

REQUIRED_FIELDS = [
    "claimant_name",
    "policy_number",
    "incident_date",
    "claim_amount",
    "incident_description",
]


class PromptTemplateManager:
    """Holds this project's prompt templates by name, so a template can be
    tuned in one place instead of being hardcoded inline at each call site."""

    def __init__(self):
        self.templates = {
            "extract_info": """Extract the following information from this insurance claim document:
- claimant_name
- policy_number
- incident_date (ISO format YYYY-MM-DD if determinable, otherwise as written)
- claim_amount (numeric, no currency symbol)
- incident_description (1-2 sentence factual summary of what happened)

Document:
{document_text}

Return ONLY a JSON object with exactly these five keys, no other text.""",
            "generate_summary": """Based on this extracted claim information and the relevant policy excerpt,
write a concise 2-3 sentence claim summary suitable for an adjuster's queue. Mention
whether the claim amount appears to fall within the policy's relevant coverage limit.

Extracted claim info:
{extracted_info}

Relevant policy excerpt:
{policy_excerpt}""",
        }

    def get_prompt(self, template_name, **kwargs):
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")
        return template.format(**kwargs)


class ModelInvoker:
    """Thin wrapper around Bedrock's Converse API so every call in this
    project goes through one place with consistent error handling."""

    def __init__(self, client):
        self.client = client

    def invoke(self, model_id, prompt, temperature=0.0, max_tokens=1000):
        response = self.client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": temperature, "maxTokens": max_tokens},
        )
        return response["output"]["message"]["content"][0]["text"]


class ContentValidator:
    """Checks the extraction step's JSON actually has all required fields
    and that they look plausible, before the summary step runs on it."""

    @staticmethod
    def validate_extraction(data):
        errors = []
        for field in REQUIRED_FIELDS:
            if field not in data or data[field] in (None, ""):
                errors.append(f"missing field: {field}")

        if "claim_amount" in data and data["claim_amount"] not in (None, ""):
            try:
                float(str(data["claim_amount"]).replace(",", "").replace("$", ""))
            except ValueError:
                errors.append(f"claim_amount does not look numeric: {data['claim_amount']!r}")

        if "incident_date" in data and data["incident_date"]:
            if not re.search(r"\d{4}", str(data["incident_date"])):
                errors.append(f"incident_date has no recognizable year: {data['incident_date']!r}")

        return {"valid": len(errors) == 0, "errors": errors}


def extract_json(raw_text):
    """Bedrock sometimes wraps JSON in prose or code fences; pull out the
    first {...} block rather than assuming the whole response is bare JSON."""
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output: {raw_text[:200]}")
    return json.loads(match.group(0))


def find_policy_excerpt(bucket, policy_number):
    """Simple RAG component: for a PoC-sized policy set, matching by policy
    number directly against the small set of stored policy documents finds
    the same result a managed retrieval index would, without needing one."""
    try:
        obj = s3.get_object(Bucket=bucket, Key=f"policies/{policy_number}.txt")
        return obj["Body"].read().decode("utf-8")
    except s3.exceptions.NoSuchKey:
        return None
    except Exception as e:
        if "NoSuchKey" in str(e):
            return None
        raise


def process_document(bucket, key, model_id=DEFAULT_MODEL):
    prompts = PromptTemplateManager()
    invoker = ModelInvoker(bedrock_runtime)
    validator = ContentValidator()

    document_text = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")

    extract_prompt = prompts.get_prompt("extract_info", document_text=document_text)
    raw_extraction = invoker.invoke(model_id, extract_prompt, temperature=0.0, max_tokens=500)
    extracted_info = extract_json(raw_extraction)

    validation = validator.validate_extraction(extracted_info)

    policy_excerpt = find_policy_excerpt(bucket, extracted_info.get("policy_number", ""))

    summary = None
    if validation["valid"]:
        summary_prompt = prompts.get_prompt(
            "generate_summary",
            extracted_info=json.dumps(extracted_info, indent=2),
            policy_excerpt=policy_excerpt or "No matching policy document found.",
        )
        summary = invoker.invoke(model_id, summary_prompt, temperature=0.4, max_tokens=300)

    result = {
        "source_key": key,
        "model_used": model_id,
        "extracted_info": extracted_info,
        "validation": validation,
        "policy_matched": policy_excerpt is not None,
        "summary": summary,
    }
    return result


def lambda_handler(event, context):
    results = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        if not key.startswith("raw-claims/") or not key.endswith(".txt"):
            continue

        result = process_document(bucket, key)
        results.append(result)

        out_key = "processed/" + key.split("/")[-1].replace(".txt", ".json")
        s3.put_object(
            Bucket=bucket,
            Key=out_key,
            Body=json.dumps(result, indent=2),
            ContentType="application/json",
        )

    return {"processed": len(results), "results": results}
