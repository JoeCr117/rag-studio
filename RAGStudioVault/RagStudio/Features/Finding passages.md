# Finding passages

The Search tab sends a query to one database and lists the chunks that best match it, showing exactly why each one ranked where it did. It is the retrieval half of the app on its own, without any answer being written.

## What the user can do

- **Pick a database** (it must be running, because its embedder turns the query into a vector).
- **Choose the mode:** the database's default, hybrid (vector plus keyword), or vector only.
- **Choose how many results** to return ([[Top-k]]), from a short list (3 to 50).
- **Turn on reranking** and choose how many candidates the reranker reads (20 to 100). This works only while a reranker is running, and the tick box explains why when it is unavailable.

## How it behaves

- **Vector mode** ranks chunks by [[Cosine similarity]] between the query's vector and each chunk's ([[Vector search]]).
- **Hybrid mode** also runs a keyword search ([[BM25]] in one engine, [[Full-text search]] in the other) and merges the two ranked lists with [[Reciprocal Rank Fusion]] using the same constant (60) in both engines. That way, scores from the two engines can be compared directly. See [[Hybrid search]].
- **Reranking** fetches the larger [[Candidate pool]], has a [[Cross-encoder]] score each query–chunk pair, and keeps the best ones in the new order ([[Reranking]]).
- **The results header** shows the hit count, the mode, and how long each step took: embedding the query, searching and reranking.
- **A legend under the header** explains the scores in plain words, for the mode in use. For example, it says the fusion score's maximum is about 0.033.
- **Each result card shows:**
  - its rank;
  - its fusion or cosine score, its raw similarity and its [[Rerank score]] when reranked;
  - in hybrid mode, its place in the vector and keyword lists;
  - its source, file path and chunk number;
  - its full text.

## Related ideas

- [[Search Methods]], [[Asking questions]]
