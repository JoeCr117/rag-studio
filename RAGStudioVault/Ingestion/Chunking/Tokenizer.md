# Tokenizer

The part of a model that converts text to tokens and back, using a fixed vocabulary learned when the model was trained.

- **In RAG Studio:** the chunker loads the embedding model's tokenizer, so [[Chunk size]] is measured exactly as the model will see the text.
- **Where it comes from:** downloaded from [[Hugging Face]] the first time a database using that model syncs, then cached in the models [[Docker volume]].
- **Small:** a tokenizer is a few megabytes; the model weights are the large part.
