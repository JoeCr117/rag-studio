# Cosine similarity

A score for how closely two vectors point in the same direction: 1 means the same direction, 0 unrelated and below 0 opposite.

- **Why direction:** an embedding's direction encodes its meaning; its length mostly does not (see [[Vector norm]]).
- **Typical values:** for text embeddings a good match is often 0.5 to 0.8, and even unrelated text rarely scores near 0.
- **Compare within one model only:** scores from different [[Embedding model|embedding models]] are on different scales.
- **In results:** the similarity pill on every hit, and the score itself in Vector only mode.
