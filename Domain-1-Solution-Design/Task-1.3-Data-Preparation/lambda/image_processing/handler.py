import json
import os

import boto3

s3 = boto3.client("s3")
textract = boto3.client("textract")
rekognition = boto3.client("rekognition")


def handler(event, context):
    results = []
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if not key.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        text_response = textract.detect_document_text(
            Document={"S3Object": {"Bucket": bucket, "Name": key}}
        )
        extracted_text = "\n".join(
            b["Text"] for b in text_response["Blocks"] if b["BlockType"] == "LINE"
        )

        label_response = rekognition.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MaxLabels=10,
            MinConfidence=60,
        )

        rekog_text_response = rekognition.detect_text(
            Image={"S3Object": {"Bucket": bucket, "Name": key}}
        )

        file_name = os.path.basename(key)
        product_id = file_name.split("_")[0] if "_" in file_name else ""

        processed_image = {
            "image_key": key,
            "extracted_text": extracted_text,
            "labels": [
                {"name": l["Name"], "confidence": round(l["Confidence"], 1)}
                for l in label_response["Labels"]
            ],
            "detected_text": [
                t["DetectedText"] for t in rekog_text_response["TextDetections"] if t["Type"] == "LINE"
            ],
            "metadata": {"product_id": product_id},
        }

        ext = os.path.splitext(key)[1]
        processed_key = key.replace("raw-data/images", "processed-data/images").replace(
            ext, "_processed.json"
        )
        s3.put_object(
            Bucket=bucket,
            Key=processed_key,
            Body=json.dumps(processed_image),
            ContentType="application/json",
        )
        results.append({"key": processed_key, "labels": len(processed_image["labels"])})

    return {"statusCode": 200, "body": json.dumps(results)}
