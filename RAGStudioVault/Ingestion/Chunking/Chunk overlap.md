# Chunk overlap

How many tokens at the end of one chunk are repeated at the start of the next, so an idea that straddles a cut appears whole in at least one chunk.

- **Trade-off:** more overlap means fewer ideas split in half, but more chunks, more storage and near-duplicate search results.
- **Typical:** 10 to 20 percent of the [[Chunk size]]. The default here is 40 tokens against a 400-token maximum.
- **Zero:** each token is stored once; fine for text whose paragraphs stand alone.
- **Changing it:** the database needs a [[Rebuild]].
