# Rebuild

Deleting and remaking every vector in a database, needed when a setting that shapes the vectors changes.

- **Triggered by changing:** the [[Vector engine]], [[Embedding model]], [[Chunk size]] or [[Chunk overlap]].
- **Why:** vectors from different models or chunkings are not comparable, so old and new cannot be mixed in one database.
- **When it happens:** the database shows a warning, and the next Sync all drops and rebuilds it.
- **Cost:** every file is read and embedded again, which can take a while on a CPU (central processing unit).
