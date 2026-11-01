# HNSW index

Hierarchical Navigable Small World, an index that finds the nearest vectors quickly by hopping through a layered graph of neighbours instead of comparing the question with every vector.

- **How:** sparse top layers make long jumps across the data; lower, denser layers refine the search, like zooming in on a map.
- **Approximate:** it can occasionally miss the true nearest vector, in exchange for searches that stay fast as the database grows.
- **Used by:** [[pgvector]] and [[Qdrant]].
- **Dimension limit in pgvector:** 2,000, or 4,000 with [[halfvec]].
