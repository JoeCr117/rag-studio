# Qdrant

A database built only for vectors, with filtering, sparse vectors and result fusion built in.

- **Hybrid in one query:** each chunk stores a dense vector from the [[Embedding model]] (every number filled in) and a sparse [[BM25]] vector, and Qdrant fuses both with [[Reciprocal Rank Fusion]] itself.
- **Index:** an [[HNSW index]], like pgvector.
- **Dashboard:** a web view of its collections at localhost port 6333, path /dashboard.
- **In RAG Studio:** each database is one collection.
