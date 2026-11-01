# Rerank score

The reranker's relevance score for one chunk, from 0 (unrelated) to 1 (answers the question); reranked results are ordered by it.

- **Absolute, not relative:** unlike the [[Reciprocal Rank Fusion]] score, it judges each chunk on its own, so 0.9 means strongly relevant whatever else was found.
- **Low across the board:** a hint that the database does not contain the answer.
- **In results:** the purple rerank pill.
