# Vector Databases

A vector database stores each chunk with its vector and finds the vectors nearest to a question's; RAG Studio offers two engines for this.

- [[Vector engine]] — the program behind a database: pgvector or Qdrant
- [[pgvector]] — vectors inside Postgres
- [[Qdrant]] — a database built only for vectors
- [[HNSW index]] — how nearest vectors are found quickly
- [[halfvec]] — half-size vectors for large models
- [[Document]] — one stored file and its chunks
- [[Rebuild]] — remaking every vector after a settings change
