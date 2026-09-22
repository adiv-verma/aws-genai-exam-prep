Now, you will have an opportunity to build a complete Retrieval Augmented Generation (RAG) system that leverages advanced vector store solutions to augment foundation models.

You'll create a knowledge assistant that can answer questions about technical documentation, research papers, and company policies while maintaining context awareness and providing accurate, up-to-date information.

Bonus assignments are an open-ended way for you to assess your overall knowledge of this task. You can share your answers on social media and tag #awsexamprep for us to review.
Bonus assignment
Project architecture overview
Phase 1: Set Up Foundation Model and vector database infrastructure
Objective: Create the core infrastructure for your RAG system using Amazon Bedrock and vector databases.

Tasks:

Set up Amazon Bedrock access:
Enable Amazon Bedrock in your AWS account
Request access to foundation models (Claude, Titan, etc.)
Create an IAM role with appropriate permissions
Create a vector database using Amazon Bedrock Knowledge Bases:
Set up a new Knowledge Base in Amazon Bedrock
Configure storage options (S3 bucket for documents)
Select an appropriate embedding model
Configure retrieval settings (number of results, similarity threshold)
Set up an alternative vector store using OpenSearch Service:
Deploy an Amazon OpenSearch Service domain
Enable the Neural Search plugin
Configure appropriate instance types and storage
Set up initial index settings and mappings for vector search
Create a metadata database using DynamoDB:
Design a schema for document metadata
Create a DynamoDB table with appropriate partition and sort keys
Configure capacity mode (on-demand or provisioned)
Phase 2: Develop document processing and embedding pipeline
Objective: Build a robust pipeline to process documents, extract metadata, and generate vector embeddings.

Tasks:

Create an S3 bucket for document storage:
Set up appropriate bucket policies and encryption
Create folders for different document types (technical docs, research papers, policies)
Implement document processing with AWS Lambda:
Create a Lambda function triggered by S3 object creation
Extract text content from various document formats (PDF, DOCX, HTML)
Implement chunking strategies (fixed size, semantic paragraphs, sliding window)
Extract and generate metadata from documents
Build an embedding generation pipeline:
Use Amazon Bedrock embedding models to generate vector embeddings
Store embeddings in your vector database (Knowledge Base or OpenSearch)
Implement batch processing for efficient embedding generation
Create a mechanism to track embedding status in DynamoDB
Develop a metadata enrichment process:
Extract document properties (creation date, author, title)
Generate additional metadata (document length, reading level, topic classification)
Store enriched metadata in DynamoDB
Create relationships between chunks and parent documents
Phase 3: Implement advanced vector search capabilities
Objective: Optimize vector search performance and implement advanced retrieval strategies.

Tasks:

Configure hierarchical indexing in OpenSearch:
Create parent-child relationships between document sections
Implement nested fields for hierarchical document structures
Configure appropriate mappings for efficient querying
Implement multi-index search strategies:
Create separate indices for different document types
Develop a search coordinator that queries multiple indices
Implement relevance scoring across indices
Create a result merging strategy
Optimize vector search performance:
Configure appropriate sharding based on data volume
Implement approximate nearest neighbor (ANN) search
Set up caching mechanisms for frequent queries
Create performance monitoring using CloudWatch
Develop advanced query processing:
Implement query expansion techniques
Create filters based on metadata attributes
Develop hybrid search combining keyword and semantic search
Implement re-ranking of search results
Phase 4: Build integration components for multiple data sources
Objective: Create connectors to integrate various data sources into your vector store.

Tasks:

Implement a web crawler for public documentation:
Create a Lambda function to crawl specified websites
Extract content and metadata from web pages
Process and store the extracted content in your pipeline
Implement rate limiting and politeness policies
Build a connector for internal wiki systems:
Create an API integration with common wiki platforms (Confluence, MediaWiki)
Implement authentication and authorization
Set up webhook listeners for real-time updates
Process wiki-specific formatting and structures
Develop a document management system connector:
Create integration with enterprise DMS systems (SharePoint, Documentum)
Implement secure access patterns
Extract document metadata and permissions
Maintain document hierarchy and relationships
Create a unified data catalog:
Develop a central registry of all data sources
Implement source-specific processing rules
Create a unified metadata schema across sources
Build a dashboard for data source management
Phase 5: Implement data maintenance and synchronization
Objective: Ensure your vector store remains current and accurate with automated maintenance.

Tasks:

Develop a change detection system:
Create checksums or version tracking for documents
Implement comparison logic to detect meaningful changes
Set up notifications for detected changes
Create a prioritization system for updates
Build an incremental update pipeline:
Develop logic to process only changed documents
Implement delta updates for modified sections
Create a system to track update status
Set up error handling and retry mechanisms
Create scheduled refresh workflows:
Implement AWS Step Functions for orchestration
Set up EventBridge rules for scheduling
Create different schedules based on data source importance
Implement resource-efficient batch processing
Develop monitoring and alerting:
Create CloudWatch dashboards for system health
Set up alerts for failed updates or stale data
Implement data freshness metrics
Create audit logs for compliance
Phase 6: Build the RAG application
Objective: Create a complete RAG application that uses your vector store to augment foundation model responses.

Tasks:

Implement the retrieval component:
Create a query processing pipeline
Develop context window optimization
Implement relevance filtering
Create a caching mechanism for frequent queries
Build the foundation model integration:
Set up Amazon Bedrock API integration
Implement prompt engineering techniques
Create a context assembly mechanism
Develop response generation logic
Create a user interface:
Build a simple web interface using AWS Amplify
Implement conversation history
Create visualization for source documents
Add feedback mechanisms for response quality
Implement analytics and improvement:
Track query performance and relevance
Create a feedback loop for continuous improvement
Implement A/B testing for different retrieval strategies
Develop user behavior analytics
Implementation details
Phase 1: Vector database setup
Amazon Bedrock Knowledge Base setup:


import boto3
import json

# Initialize Bedrock client
bedrock = boto3.client('bedrock')

# Create a Knowledge Base
response = bedrock.create_knowledge_base(
    name="TechnicalDocumentationKB",
    description="Knowledge base for technical documentation",
    roleArn="arn:aws:iam::123456789012:role/BedrockKBRole",
    knowledgeBaseConfiguration={
        "type": "VECTOR",
        "vectorKnowledgeBaseConfiguration": {
            "embeddingModelArn": "arn:aws:bedrock:us-east-1::embeddings/amazon.titan-embed-text-v1"
        }
    }
)

knowledge_base_id = response['knowledgeBase']['knowledgeBaseId']
print(f"Created Knowledge Base with ID: {knowledge_base_id}")

# Create a data source for the Knowledge Base
response = bedrock.create_data_source(
    knowledgeBaseId=knowledge_base_id,
    name="TechnicalDocsSource",
    description="Technical documentation source",
    dataSourceConfiguration={
        "type": "S3",
        "s3Configuration": {
            "bucketArn": "arn:aws:s3:::technical-docs-bucket",
            "inclusionPrefixes": ["documentation/"]
        }
    },
    vectorIngestionConfiguration={
        "chunkingConfiguration": {
            "chunkingStrategy": "SEMANTIC_CHUNKING",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 300,
                "overlapPercentage": 10
            }
        }
    }
)

data_source_id = response['dataSource']['dataSourceId']
print(f"Created Data Source with ID: {data_source_id}")
OpenSearch Service setup:


# CloudFormation template excerpt for OpenSearch Service
Resources:
  OpenSearchServiceDomain:
    Type: AWS::OpenSearch::Domain
    Properties:
      DomainName: vector-search-domain
      EngineVersion: OpenSearch_2.11
      ClusterConfig:
        InstanceType: r6g.large.search
        InstanceCount: 3
        ZoneAwarenessEnabled: true
        ZoneAwarenessConfig:
          AvailabilityZoneCount: 3
      EBSOptions:
        EBSEnabled: true
        VolumeType: gp3
        VolumeSize: 100
      AdvancedOptions:
        "rest.action.multi.allow_explicit_index": "true"
        "plugins.ml_commons.only_run_on_ml_node": "false"
      AccessPolicies:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              AWS: !GetAtt LambdaExecutionRole.Arn
            Action: "es:*"
            Resource: !Sub "arn:aws:es:${AWS::Region}:${AWS::AccountId}:domain/vector-search-domain/*"
      AdvancedSecurityOptions:
        Enabled: true
        InternalUserDatabaseEnabled: true
        MasterUserOptions:
          MasterUserName: admin
          MasterUserPassword: !Ref MasterUserPassword
      NodeToNodeEncryptionOptions:
        Enabled: true
      EncryptionAtRestOptions:
        Enabled: true
      DomainEndpointOptions:
        EnforceHTTPS: true
      PluginOptions:
        - PluginName: "ml-commons"
          Enabled: true
        - PluginName: "neural-search"
          Enabled: true
DynamoDB metadata table setup:


import boto3

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb')

# Create table for document metadata
response = dynamodb.create_table(
    TableName='DocumentMetadata',
    KeySchema=[
        {
            'AttributeName': 'document_id',
            'KeyType': 'HASH'  # Partition key
        },
        {
            'AttributeName': 'chunk_id',
            'KeyType': 'RANGE'  # Sort key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'document_id',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'chunk_id',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'document_type',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'last_updated',
            'AttributeType': 'S'
        }
    ],
    GlobalSecondaryIndexes=[
        {
            'IndexName': 'DocumentTypeIndex',
            'KeySchema': [
                {
                    'AttributeName': 'document_type',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'last_updated',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL'
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
    ],
    BillingMode='PAY_PER_REQUEST'
)

print(f"Created DynamoDB table: {response['TableDescription']['TableName']}")
Phase 2: Document processing pipeline
Lambda Function for document processing


import boto3
import json
import os
import uuid
import hashlib
from datetime import datetime
import PyPDF2
import docx
import io
import re

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')

metadata_table = dynamodb.Table('DocumentMetadata')

def lambda_handler(event, context):
    # Get the S3 bucket and key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Generate a unique document ID
    document_id = str(uuid.uuid4())
    
    # Extract file metadata
    response = s3.head_object(Bucket=bucket, Key=key)
    content_type = response.get('ContentType', '')
    last_modified = response.get('LastModified').strftime('%Y-%m-%dT%H:%M:%S')
    
    # Download the document
    response = s3.get_object(Bucket=bucket, Key=key)
    document_content = response['Body'].read()
    
    # Extract text based on file type
    if key.lower().endswith('.pdf'):
        text = extract_text_from_pdf(document_content)
        document_type = 'pdf'
    elif key.lower().endswith('.docx'):
        text = extract_text_from_docx(document_content)
        document_type = 'docx'
    elif key.lower().endswith('.txt'):
        text = document_content.decode('utf-8')
        document_type = 'txt'
    else:
        raise ValueError(f"Unsupported file type: {key}")
    
    # Generate document checksum for change detection
    checksum = hashlib.md5(document_content).hexdigest()
    
    # Extract basic metadata
    title = os.path.basename(key)
    author = response.get('Metadata', {}).get('author', 'Unknown')
    
    # Create document chunks using semantic chunking
    chunks = create_semantic_chunks(text)
    
    # Store document metadata in DynamoDB
    base_metadata = {
        'document_id': document_id,
        'title': title,
        'author': author,
        'document_type': document_type,
        'source_bucket': bucket,
        'source_key': key,
        'content_type': content_type,
        'last_updated': last_modified,
        'checksum': checksum,
        'total_chunks': len(chunks)
    }
    
    # Process each chunk
    for i, chunk in enumerate(chunks):
        chunk_id = f"{document_id}-{i}"
        
        # Generate embedding for the chunk
        embedding = generate_embedding(chunk)
        
        # Store chunk metadata
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            'chunk_id': chunk_id,
            'chunk_index': i,
            'chunk_text': chunk,
            'chunk_length': len(chunk),
            'embedding_status': 'completed'
        })
        
        metadata_table.put_item(Item=chunk_metadata)
        
        # Store embedding in vector database (implementation depends on chosen vector store)
        store_embedding_in_vector_db(chunk_id, embedding, chunk, chunk_metadata)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'document_id': document_id,
            'chunks_processed': len(chunks)
        })
    }

def extract_text_from_pdf(pdf_content):
    pdf_file = io.BytesIO(pdf_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

def extract_text_from_docx(docx_content):
    docx_file = io.BytesIO(docx_content)
    doc = docx.Document(docx_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def create_semantic_chunks(text, max_chunk_size=1000, overlap=100):
    # Simple implementation - in production, use more sophisticated semantic chunking
    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            # Include overlap from the previous chunk
            overlap_text = " ".join(current_chunk.split()[-overlap:]) if overlap > 0 else ""
            current_chunk = overlap_text + " " + sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def generate_embedding(text):
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "inputText": text
        })
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['embedding']

def store_embedding_in_vector_db(chunk_id, embedding, text, metadata):
    # Implementation depends on chosen vector database (OpenSearch or Bedrock KB)
    # This is a placeholder for the actual implementation
    pass
Phase 3: Advanced vector search implementation
OpenSearch index configuration for hierarchical documents:


import boto3
import requests
from requests_aws4auth import AWS4Auth
import json

region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 
                   region, service, session_token=credentials.token)

host = 'https://your-opensearch-domain.us-east-1.es.amazonaws.com'
index_name = 'technical_documentation'
url = host + '/' + index_name

# Define the index mapping with hierarchical structure
index_mapping = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100
        }
    },
    "mappings": {
        "properties": {
            "document_id": {"type": "keyword"},
            "parent_id": {"type": "keyword"},
            "title": {"type": "text"},
            "content": {"type": "text"},
            "metadata": {
                "properties": {
                    "author": {"type": "keyword"},
                    "created_date": {"type": "date"},
                    "document_type": {"type": "keyword"},
                    "department": {"type": "keyword"},
                    "tags": {"type": "keyword"}
                }
            },
            "embedding": {
                "type": "knn_vector",
                "dimension": 1536,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib",
                    "parameters": {
                        "ef_construction": 128,
                        "m": 16
                    }
                }
            },
            "hierarchy": {
                "type": "nested",
                "properties": {
                    "level": {"type": "keyword"},
                    "path": {"type": "keyword"},
                    "position": {"type": "integer"}
                }
            }
        }
    }
}

# Create the index
response = requests.put(url, auth=awsauth, json=index_mapping, headers={"Content-Type": "application/json"})
print(response.text)

# Function to search across multiple indices with metadata filtering
def search_documents(query_text, filters=None, indices=None):
    if indices is None:
        indices = ["technical_documentation", "research_papers", "company_policies"]
    
    # Generate embedding for the query
    bedrock = boto3.client('bedrock-runtime')
    embedding_response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": query_text})
    )
    
    embedding = json.loads(embedding_response['body'].read())['embedding']
    
    # Build the search query
    search_query = {
        "size": 10,
        "query": {
            "bool": {
                "must": [
                    {
                        "knn": {
                            "embedding": {
                                "vector": embedding,
                                "k": 10
                            }
                        }
                    }
                ]
            }
        }
    }
    
    # Add filters if provided
    if filters:
        filter_clauses = []
        for key, value in filters.items():
            if key.startswith("metadata."):
                filter_clauses.append({"term": {key: value}})
        
        if filter_clauses:
            search_query["query"]["bool"]["filter"] = filter_clauses
    
    # Execute search across multiple indices
    search_url = host + '/' + ','.join(indices) + '/_search'
    response = requests.post(search_url, auth=awsauth, json=search_query, headers={"Content-Type": "application/json"})
    
    return json.loads(response.text)
Phase 4: Integration component for wiki systems


import boto3
import requests
import json
import os
import base64
from datetime import datetime

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('