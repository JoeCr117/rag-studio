# Cross-encoder

A model that reads the question and one chunk together and outputs a single relevance score, instead of turning each into a vector separately.

- **Why more accurate:** it sees how the question's words relate to the chunk's words directly, while an [[Embeddings|embedding]] squeezes each text into one vector before they meet.
- **Why slower:** it runs once per question-and-chunk pair, so it cannot scan a whole database. Embeddings are computed once, ahead of time.
- **In RAG Studio:** Qwen3-Reranker 0.6B, run by [[llama.cpp]] on the CPU (central processing unit) or GPU (graphics processing unit).
- **Gives:** the [[Rerank score]].
