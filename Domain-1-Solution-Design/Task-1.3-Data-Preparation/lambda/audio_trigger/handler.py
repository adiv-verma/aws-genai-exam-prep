import json
import os
import uuid

import boto3

sfn = boto3.client("stepfunctions")

STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if not key.lower().endswith((".mp3", ".wav", ".flac")):
            continue

        base = os.path.splitext(os.path.basename(key))[0]
        job_name = f"adi-1-3-{base}-{uuid.uuid4().hex[:8]}"
        output_key = key.replace("raw-data/audio", "transcriptions").replace(
            os.path.splitext(key)[1], ".json"
        )

        sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=job_name,
            input=json.dumps(
                {
                    "bucket": bucket,
                    "audio_key": key,
                    "job_name": job_name,
                    "output_key": output_key,
                    "media_format": os.path.splitext(key)[1][1:],
                }
            ),
        )

    return {"statusCode": 200}
