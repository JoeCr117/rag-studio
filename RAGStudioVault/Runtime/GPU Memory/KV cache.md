# KV cache

The key-value (KV) cache: memory where a model keeps intermediate results for every token it has read, so each new token does not recompute the whole prompt.

- **Grows with the [[Context window]]:** it is reserved for the full window, so a bigger window costs more [[VRAM]] (video random-access memory) before it is used.
- **In RAG Studio:** stored at 8-bit precision (q8_0), half the size of 16 bits with almost no loss.
- **Shown as:** the VRAM estimate at 8k context on each generator.
