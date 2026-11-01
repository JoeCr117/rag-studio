# pgvector

An extension that adds vector columns and nearest-vector search to Postgres, the widely used open-source relational database.

- **Why use it:** vectors sit next to ordinary tables and Postgres [[Full-text search]], queried with SQL (Structured Query Language).
- **Index:** an [[HNSW index]] using cosine distance.
- **Limit:** the index covers up to 2,000 dimensions; larger vectors are stored as [[halfvec]].
- **In RAG Studio:** the pgvector service, reachable from Windows on port 5434.
