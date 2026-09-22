"""
adi-1-5-embedding-generator

Manually invoked (batch job, no event trigger — same "no idle cost" pattern
as Task 1.4's search-coordinator Lambda). Reads every chunk produced by
adi-1-5-chunking-engine under chunks/{strategy}/{doc_id}/, generates an
embedding for each chunk with BOTH Amazon Titan and Cohere Embed, and writes
the results under embeddings/{model}/{strategy}/{doc_id}/ so the retrieval
evaluator can compare all (strategy x model) combinations later.
"""
import boto3
import json
import os

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

TITAN_MODEL_ID = 'amazon.titan-embed-text-v1'
COHERE_MODEL_ID = 'cohere.embed-english-v3'
COHERE_BATCH_SIZE = 20  # matches project.md's own sample batch size


def list_all_chunk_keys(bucket):
    keys = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix='chunks/'):
        for obj in page.get('Contents', []):
            if obj['Key'].endswith('.json'):
                keys.append(obj['Key'])
    return keys


def load_chunk(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read().decode('utf-8'))


def embed_titan(text):
    response = bedrock.invoke_model(
        modelId=TITAN_MODEL_ID,
        contentType='application/json',
        accept='application/json',
        body=json.dumps({'inputText': text})
    )
    return json.loads(response['body'].read())['embedding']


def embed_cohere_batch(texts):
    """Cohere natively accepts a batch of texts in one call — this is the
    'batch processing for efficiency' step project.md's Phase 2 Step 2 asks
    for, versus Titan which only accepts one input per call."""
    response = bedrock.invoke_model(
        modelId=COHERE_MODEL_ID,
        contentType='application/json',
        accept='application/json',
        body=json.dumps({'texts': texts, 'input_type': 'search_document'})
    )
    return json.loads(response['body'].read())['embeddings']


def write_embedding(bucket, model_name, chunk):
    strategy = chunk['strategy']
    doc_id = chunk['doc_id']
    idx = chunk['chunk_index']
    key = f'embeddings/{model_name}/{strategy}/{doc_id}/chunk_{idx:03d}.json'
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(chunk).encode('utf-8'),
        ContentType='application/json'
    )
    return key


def lambda_handler(event, context):
    bucket = event.get('bucket') or os.environ.get('DOCUMENTS_BUCKET')
    chunk_keys = list_all_chunk_keys(bucket)
    chunks = [load_chunk(bucket, k) for k in chunk_keys]

    counts = {'titan': 0, 'cohere': 0, 'total_chunks': len(chunks)}

    # Titan: one call per chunk (no native batch support in this model version)
    for chunk in chunks:
        embedding = embed_titan(chunk['text'])
        out = dict(chunk)
        out['model'] = TITAN_MODEL_ID
        out['embedding'] = embedding
        out['embedding_dim'] = len(embedding)
        write_embedding(bucket, 'titan', out)
        counts['titan'] += 1

    # Cohere: batched calls of COHERE_BATCH_SIZE texts at a time
    for i in range(0, len(chunks), COHERE_BATCH_SIZE):
        batch = chunks[i:i + COHERE_BATCH_SIZE]
        texts = [c['text'] for c in batch]
        embeddings = embed_cohere_batch(texts)
        for chunk, embedding in zip(batch, embeddings):
            out = dict(chunk)
            out['model'] = COHERE_MODEL_ID
            out['embedding'] = embedding
            out['embedding_dim'] = len(embedding)
            write_embedding(bucket, 'cohere', out)
            counts['cohere'] += 1

    print(json.dumps(counts))
    return counts
