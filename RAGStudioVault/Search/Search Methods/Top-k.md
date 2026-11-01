# Top-k

How many chunks a search returns, the top k by score; the Results setting on the Search and Ask tabs.

- **Search tab:** more results show more of what matched.
- **Ask tab:** the results become the generator's [[Passages]]. More passages raise the chance the answer is among them, but cost [[Prefill]] time and room in the [[Context window]], and can distract the model.
- **Typical for answers:** 3 to 8.
- **With reranking:** the [[Candidate pool]] is fetched first, then the reranker keeps the best k.
