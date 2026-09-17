import json

import boto3

s3 = boto3.client("s3")
comprehend = boto3.client("comprehend")


def handler(event, context):
    bucket = event["bucket"]
    audio_key = event["audio_key"]
    output_key = event["output_key"]

    response = s3.get_object(Bucket=bucket, Key=output_key)
    transcription = json.loads(response["Body"].read().decode("utf-8"))
    transcript = transcription["results"]["transcripts"][0]["transcript"]

    sentiment_response = comprehend.detect_sentiment(Text=transcript, LanguageCode="en")
    key_phrases_response = comprehend.detect_key_phrases(Text=transcript, LanguageCode="en")

    processed_call = {
        "audio_key": audio_key,
        "transcript": transcript,
        "speakers": transcription["results"].get("speaker_labels", {}).get("segments", []),
        "sentiment": sentiment_response["Sentiment"],
        "sentiment_scores": sentiment_response["SentimentScore"],
        "key_phrases": [kp["Text"] for kp in key_phrases_response["KeyPhrases"]],
        "metadata": {"call_id": event["job_name"]},
    }

    import os

    processed_key = audio_key.replace("raw-data/audio", "processed-data/audio").replace(
        os.path.splitext(audio_key)[1], "_processed.json"
    )
    s3.put_object(
        Bucket=bucket,
        Key=processed_key,
        Body=json.dumps(processed_call),
        ContentType="application/json",
    )

    return {"processed_key": processed_key, "sentiment": sentiment_response["Sentiment"]}
