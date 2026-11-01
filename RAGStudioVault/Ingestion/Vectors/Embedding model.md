# Embedding model

A language model trained to output one vector per text instead of writing words; it decides how well search understands meaning.

- **Choices here:** Qwen3-Embedding 0.6B (small and fast), Qwen3-Embedding 4B (more accurate, slower), nomic-embed-text v1.5 (tiny, English) and BGE-M3 (multilingual).
- **Trade-off:** bigger models place meanings more precisely but embed more slowly, especially on the CPU (central processing unit).
- **What differs between them:** [[Dimensions]], [[Pooling]] and whether they expect an [[Instruction prefix]].
- **Runs as:** an [[Embedder]] container.
- **Stored as:** a [[GGUF]] file in the models [[Docker volume]].
- **Changing it:** every vector must be remade, so the database needs a [[Rebuild]].
