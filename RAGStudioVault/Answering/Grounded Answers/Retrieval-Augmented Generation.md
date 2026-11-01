# Retrieval-Augmented Generation

Answering a question by first searching your documents for relevant passages and then having a language model write the answer from those passages alone.

- **Also called:** RAG.
- **Why:** a model's training knows nothing about your files, and a whole folder will not fit in its [[Context window]]. Retrieval hands it only what matters.
- **Steps in RAG Studio:** search the database ([[Hybrid search]], optionally [[Reranking]]), number the top chunks as [[Passages]], and ask the [[Generator]] to answer citing them.
- **Grounding:** the model is told to use only the passages and to say it does not know otherwise, which reduces made-up answers.
- **Quality depends mostly on retrieval:** if the right chunk is not among the passages, the generator cannot use it.
