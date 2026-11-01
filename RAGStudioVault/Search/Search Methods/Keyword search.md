# Keyword search

Finding the chunks that contain the question's words, ranked by how often those words appear and how rare they are.

- **Strength:** exact names, product codes, error messages and rare terms.
- **Weakness:** it does not know synonyms, so car does not find automobile.
- **In pgvector databases:** Postgres [[Full-text search]].
- **In Qdrant databases:** [[BM25]], computed by Qdrant.
- **Combined with meaning:** see [[Hybrid search]].
