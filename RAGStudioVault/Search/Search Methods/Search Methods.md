# Search Methods

The ways RAG Studio finds chunks for a question, and how their results are scored and merged.

- [[Vector search]] — finding chunks by meaning
- [[Cosine similarity]] — the score for how alike two vectors are
- [[Keyword search]] — finding chunks by their words
- [[Full-text search]] — Postgres's built-in keyword search
- [[BM25]] — the keyword-ranking formula Qdrant uses
- [[Hybrid search]] — meaning and words together
- [[Reciprocal Rank Fusion]] — merging two ranked lists by position
- [[Top-k]] — how many results come back
