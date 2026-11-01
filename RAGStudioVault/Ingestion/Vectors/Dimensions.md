# Dimensions

How many numbers are in each vector an embedding model produces, such as 768, 1,024 or 2,560.

- **More dimensions:** room to encode finer distinctions in meaning, but more storage and slower comparisons.
- **Fixed per model:** every vector in one database has the same length, because they all come from one [[Embedding model]].
- **Index limit:** [[pgvector]]'s [[HNSW index]] covers at most 2,000 dimensions of full-precision vectors, so larger ones are stored as [[halfvec]].
- **In the Browse tab:** the dims pill on each chunk.
