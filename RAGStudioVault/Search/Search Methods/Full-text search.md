# Full-text search

Postgres's built-in keyword search: text is reduced to word stems with common words dropped, and chunks are ranked by how well their stems match the question's.

- **Stemming:** running and runs both become run, so different forms of a word match.
- **Stop words:** words such as the and of are ignored, because they match everything.
- **English configuration:** a rule-based Snowball stemmer and an English stop-word list, both inside the [[pgvector]] image (see [[Docker image]]).
- **Any word may match:** RAG Studio joins the question's words with OR, so a chunk matching only some of them still ranks.
- **Used by:** [[Hybrid search]] in pgvector databases.
