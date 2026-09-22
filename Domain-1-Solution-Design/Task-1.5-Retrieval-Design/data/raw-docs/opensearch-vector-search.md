# Amazon OpenSearch Vector Search

Amazon OpenSearch Service supports vector search through the k-NN plugin, allowing an index to store dense vector embeddings alongside traditional text fields and to combine both in a single query for hybrid search.

## The k-NN plugin and vector fields

An OpenSearch index field of type knn_vector stores a fixed-dimension floating-point vector for each document. At index-creation time the field mapping specifies the vector's dimension and the algorithm used to search it. The two most common algorithms are HNSW (Hierarchical Navigable Small World graphs), which builds a graph structure for fast approximate nearest-neighbor search, and IVF, which partitions the vector space into clusters searched selectively. HNSW generally offers better recall and query latency at the cost of higher memory usage during indexing, and is the default choice for most workloads.

## Approximate versus exact k-NN

OpenSearch supports both approximate k-NN, which trades a small amount of recall for large gains in query speed at scale, and exact (brute-force) k-NN, which computes the true nearest neighbors by scanning every vector in the index. Exact k-NN is only practical for smaller indexes, typically under a few tens of thousands of vectors, because its query time grows linearly with the number of documents. Approximate k-NN using HNSW or IVF is what makes OpenSearch practical for indexes with millions of vectors, since query time stays roughly constant as the index grows.

## Hybrid search

Hybrid search in OpenSearch combines a k-NN vector query with a traditional BM25 keyword query in a single search request, then normalizes and blends the two sets of relevance scores. This is important because pure vector search can miss exact matches on identifiers, product codes, or rare proper nouns that a keyword search would catch immediately, while pure keyword search misses conceptually related results that use different wording than the query. The neural-search plugin can also generate the query vector automatically from raw query text at search time, using a configured embedding model, so the calling application does not need to compute the query embedding itself.

## Sharding and replicas for vector indexes

Vector indexes benefit from the same sharding principles as any OpenSearch index: splitting a large index into multiple shards distributes both the indexing and query load across nodes, but each additional shard also adds a small amount of query overhead from result merging. For vector workloads specifically, the HNSW graph structure for each shard is held largely in memory, so the number of shards and their size directly affects the memory required on each data node, and is usually the dominant factor in cluster sizing decisions.

## Quantization and cost

Because floating-point vectors are memory-intensive at scale, OpenSearch supports storing vectors in reduced-precision formats such as byte-quantized or binary vectors, which can reduce memory footprint substantially with a manageable reduction in recall accuracy. This is typically a much larger cost lever than instance-type selection alone, since vector index memory usage is often the binding constraint on cluster size for large corpora.
