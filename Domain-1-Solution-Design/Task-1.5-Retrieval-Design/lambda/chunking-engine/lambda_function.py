"""
adi-1-5-chunking-engine

S3-triggered on raw-docs/*.md uploads. Implements three chunking strategies
(fixed-size, hierarchical, semantic) over the same source document and writes
each strategy's chunks to a separate prefix, so downstream steps can compare
retrieval quality across strategies on identical source content.
"""
import boto3
import json
import re
import os
import math
import statistics

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

TITAN_MODEL_ID = 'amazon.titan-embed-text-v1'


def get_titan_embedding(text):
    response = bedrock.invoke_model(
        modelId=TITAN_MODEL_ID,
        contentType='application/json',
        accept='application/json',
        body=json.dumps({'inputText': text})
    )
    body = json.loads(response['body'].read())
    return body['embedding']


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def split_sentences(text):
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


# --- Strategy 1: Fixed-size chunking with overlap ---
def fixed_size_chunking(text, chunk_size=800, overlap=100):
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            boundary = end
            for i in range(end - 1, max(start + chunk_size // 2, start), -1):
                if text[i] in '.!?' and i + 1 < n and text[i + 1] == ' ':
                    boundary = i + 1
                    break
            end = boundary
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(chunk_text)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


# --- Strategy 2: Hierarchical (structure-aware) chunking on "## " headings ---
def hierarchical_chunking(markdown_text, doc_title):
    sections = re.split(r'\n##\s+', markdown_text)
    chunks = []
    intro = sections[0].strip()
    if intro:
        chunks.append({'text': intro, 'section_title': doc_title})
    for sec in sections[1:]:
        lines = sec.split('\n', 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ''
        chunk_text = f"{title}\n\n{body}".strip()
        chunks.append({'text': chunk_text, 'section_title': title})
    return chunks


# --- Strategy 3: Semantic chunking via consecutive-sentence similarity ---
# Splits wherever similarity between consecutive sentences drops meaningfully
# below that document's own average — a per-document statistical threshold
# (mean - 0.5*stdev) rather than one arbitrary constant across all documents,
# since embedding similarity scales differ by content.
def semantic_chunking(text, min_sentences=2, max_chunk_chars=1200, drop_std_factor=0.5):
    sentences = split_sentences(text)
    if len(sentences) <= 1:
        return [text.strip()] if text.strip() else []

    embeddings = [get_titan_embedding(s) for s in sentences]
    sims = [cosine_similarity(embeddings[i - 1], embeddings[i]) for i in range(1, len(sentences))]

    if len(sims) >= 2:
        mean_sim = statistics.mean(sims)
        stdev_sim = statistics.pstdev(sims)
    elif sims:
        mean_sim, stdev_sim = sims[0], 0.0
    else:
        mean_sim, stdev_sim = 1.0, 0.0
    threshold = mean_sim - drop_std_factor * stdev_sim

    chunks = []
    current = [sentences[0]]
    current_len = len(sentences[0])
    for i in range(1, len(sentences)):
        sim = sims[i - 1]
        would_be_len = current_len + len(sentences[i]) + 1
        is_topic_shift = sim < threshold and len(current) >= min_sentences
        too_long = would_be_len > max_chunk_chars
        if is_topic_shift or too_long:
            chunks.append(' '.join(current))
            current = [sentences[i]]
            current_len = len(sentences[i])
        else:
            current.append(sentences[i])
            current_len = would_be_len
    if current:
        chunks.append(' '.join(current))
    return chunks


def write_chunk(bucket, strategy, doc_id, idx, item):
    s3.put_object(
        Bucket=bucket,
        Key=f'chunks/{strategy}/{doc_id}/chunk_{idx:03d}.json',
        Body=json.dumps(item).encode('utf-8'),
        ContentType='application/json'
    )


def lambda_handler(event, context):
    results = {'processed': []}

    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        if not key.endswith('.md'):
            continue

        doc_id = os.path.basename(key).rsplit('.', 1)[0]
        obj = s3.get_object(Bucket=bucket, Key=key)
        text = obj['Body'].read().decode('utf-8')

        first_line = text.split('\n', 1)[0]
        doc_title = first_line.lstrip('#').strip()
        body_text = text.split('\n', 1)[1].strip() if '\n' in text else text

        counts = {}

        fixed_chunks = fixed_size_chunking(body_text, chunk_size=800, overlap=100)
        for idx, chunk_text in enumerate(fixed_chunks):
            write_chunk(bucket, 'fixed', doc_id, idx, {
                'chunk_id': f'{doc_id}-fixed-{idx:03d}',
                'doc_id': doc_id,
                'doc_title': doc_title,
                'strategy': 'fixed',
                'chunk_index': idx,
                'text': chunk_text,
                'char_count': len(chunk_text)
            })
        counts['fixed'] = len(fixed_chunks)

        hier_chunks = hierarchical_chunking(text, doc_title)
        for idx, chunk in enumerate(hier_chunks):
            write_chunk(bucket, 'hierarchical', doc_id, idx, {
                'chunk_id': f'{doc_id}-hierarchical-{idx:03d}',
                'doc_id': doc_id,
                'doc_title': doc_title,
                'strategy': 'hierarchical',
                'chunk_index': idx,
                'section_title': chunk['section_title'],
                'text': chunk['text'],
                'char_count': len(chunk['text'])
            })
        counts['hierarchical'] = len(hier_chunks)

        sem_chunks = semantic_chunking(body_text)
        for idx, chunk_text in enumerate(sem_chunks):
            write_chunk(bucket, 'semantic', doc_id, idx, {
                'chunk_id': f'{doc_id}-semantic-{idx:03d}',
                'doc_id': doc_id,
                'doc_title': doc_title,
                'strategy': 'semantic',
                'chunk_index': idx,
                'text': chunk_text,
                'char_count': len(chunk_text)
            })
        counts['semantic'] = len(sem_chunks)

        results['processed'].append({'doc_id': doc_id, 'chunk_counts': counts})

    print(json.dumps(results))
    return results
