# Embeddings

A list of numbers, a vector, that represents the meaning of a piece of text, so that texts about the same thing get vectors pointing in similar directions.

- **Made by:** an [[Embedding model]]: one vector per [[Chunk]] when syncing, one per question when searching.
- **Why it works:** the model is trained so that paraphrases land close together, which lets search find a match that shares no words with the question.
- **Compared with:** [[Cosine similarity]].
- **Size:** fixed per model; see [[Dimensions]].
- **Same model both ways:** a question must be embedded by the same model as the chunks, because each model has its own coordinate system. Changing the model needs a [[Rebuild]].
