# halfvec

pgvector's half-precision vector type: each number is stored in 16 bits instead of 32, halving the size.

- **Why RAG Studio uses it:** pgvector's [[HNSW index]] cannot index ordinary vectors above 2,000 [[Dimensions]], but can index halfvec up to 4,000.
- **When:** automatically for models above 2,000 dimensions, such as Qwen3-Embedding 4B with 2,560.
- **Cost:** a tiny loss of precision, too small to change search results in practice.
