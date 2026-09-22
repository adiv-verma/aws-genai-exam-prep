# Amazon Bedrock Knowledge Bases

Amazon Bedrock Knowledge Bases provide a fully managed way to connect foundation models to an organization's own data for Retrieval Augmented Generation, handling ingestion, chunking, embedding, and vector storage without requiring custom infrastructure.

## How a knowledge base is built

A knowledge base is created by pointing it at a data source, most commonly an S3 bucket, and selecting an embedding model such as an Amazon Titan Text Embeddings model. Bedrock automatically syncs the data source, extracting text from supported document formats, splitting it into chunks according to the configured chunking strategy, generating an embedding for each chunk, and storing the resulting vectors in a backing vector store. The entire ingestion pipeline is managed, so no custom Lambda functions or orchestration are required to keep the index up to date beyond triggering a sync when the source data changes.

## Chunking strategies

Bedrock Knowledge Bases support several built-in chunking strategies: fixed-size chunking with configurable token count and overlap percentage, hierarchical chunking that preserves parent-child relationships between larger and smaller chunks, semantic chunking that groups sentences by meaning, and a no-chunking option that treats an entire document as a single chunk. A custom Lambda function can also be registered to implement a bespoke chunking strategy for document types the built-in options do not handle well.

## Backing vector stores

A knowledge base can be backed by several vector store options: the default managed OpenSearch Serverless collection created automatically, an existing Amazon OpenSearch Service domain, Amazon Aurora with the pgvector extension, Amazon Neptune Analytics, Redis Enterprise Cloud, or MongoDB Atlas. Choosing an existing vector store rather than the default managed option is useful when the vector data needs to be shared with other applications outside of Bedrock, or when specific vector store features such as custom index tuning are required.

## Querying a knowledge base

Applications query a knowledge base either directly through the Retrieve API, which returns the most relevant chunks and their source citations, or through RetrieveAndGenerate, which additionally passes the retrieved chunks to a specified foundation model to produce a synthesized natural-language answer with citations. Retrieval can be configured to use semantic (vector-only) search or hybrid search, which combines vector similarity with keyword matching for better recall on queries containing exact terms such as product codes or proper nouns.

## Metadata filtering

Each chunk can carry metadata attributes, such as document category, publication date, or access-control tags, alongside its embedding. Queries can apply metadata filters to restrict retrieval to a relevant subset of the corpus, which both improves relevance and enforces logical separation between different categories of content stored in the same knowledge base.
