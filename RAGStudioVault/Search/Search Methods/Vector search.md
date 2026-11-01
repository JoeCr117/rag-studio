# Vector search

Finding the chunks whose vectors point in nearly the same direction as the question's vector; it matches meaning even when no words are shared.

- **Steps:** embed the question with the database's [[Embedding model]], then ask the [[Vector engine]] for the nearest chunk vectors.
- **Scored by:** [[Cosine similarity]].
- **Fast on big databases:** an [[HNSW index]] finds near neighbours without comparing every vector.
- **Strength:** paraphrases and related ideas, such as car finding automobile.
- **Weakness:** exact names, codes and rare terms, which [[Keyword search]] handles.
- **In the Mode menu:** Vector only.
