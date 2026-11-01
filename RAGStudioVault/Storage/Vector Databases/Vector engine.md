# Vector engine

The program that stores a database's chunks and vectors and runs its searches: pgvector or Qdrant in RAG Studio.

- **Same results, different machinery:** both run [[Hybrid search]] merged by [[Reciprocal Rank Fusion]] with the same settings, so you can compare them on the same files.
- **Choices:** [[pgvector]] and [[Qdrant]].
- **Storage:** each RAG Studio database is one Postgres database named vdb_ plus its number in pgvector, or one collection with that name in Qdrant.
- **Changing it:** the data is remade by a [[Rebuild]].
