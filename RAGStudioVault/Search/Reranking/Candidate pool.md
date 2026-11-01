# Candidate pool

How many search results are fetched for the reranker to re-read before the best few are kept.

- **Bigger pool:** a relevant chunk that the first search ranked 25th can still be rescued, but every extra candidate costs one more [[Cross-encoder]] pass.
- **Choices:** 20, 30, 50 or 100 candidates; the Results setting ([[Top-k]]) decides how many survive.
- **Cost shown:** the rerank time in the line above the results.
