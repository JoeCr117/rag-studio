# Hybrid search

Running a vector search and a keyword search for the same question and merging their results, so a hit can come from meaning, exact words or both.

- **Why:** [[Vector search]] misses exact names and codes; [[Keyword search]] misses paraphrases. Together they cover each other's gaps.
- **Merging:** [[Reciprocal Rank Fusion]] combines the two ranked lists by position.
- **Pool:** each method contributes its top 40 chunks before merging.
- **In results:** each hit shows its rank in both lists, such as vector #3 · keyword #1; a dash means that list did not find it.
- **Default:** a database's Search mode decides; the Mode menu overrides it for one search.
