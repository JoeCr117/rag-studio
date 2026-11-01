# Instruction prefix

A fixed phrase an embedding model expects in front of a text, telling it whether the text is a search question or a document to be found.

- **Why:** questions and passages are different kinds of text. The prefix helps the model place a short question near the long passage that answers it, which is called asymmetric retrieval.
- **Qwen3 models:** questions get an instruction (Given a search query, retrieve the passages that answer it); documents get nothing.
- **nomic-embed-text:** questions start with search_query: and documents with search_document:.
- **BGE-M3:** no prefix.
- **Added automatically:** by the embedding client. The Browse tab shows the embedded text without it.
