# Pooling

How an embedding model turns the many per-token vectors it computes inside into the single vector that represents the whole text.

- **Last:** use the vector of the final token, which has read everything before it. Used by the Qwen3 models.
- **Mean:** average all the token vectors. Used by nomic-embed-text.
- **CLS (classification token):** use a special token placed at the start for this purpose. Used by BGE-M3.
- **Not a choice:** each model was trained with one method, and another gives poor vectors, so the catalog sets it per model.
