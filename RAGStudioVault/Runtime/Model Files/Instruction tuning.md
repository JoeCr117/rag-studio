# Instruction tuning

Extra training that turns a base model, which only continues text, into one that follows requests and answers in turns. Models trained this way carry tags such as `Instruct`, `it` or `Chat` in their names.

- **Base model:** trained on a huge amount of text to predict the next word. Asked "What is RAG?", it may continue with more questions instead of answering.
- **Instruction-tuned model:** further trained on examples of requests paired with good answers, and often on human preference ratings. It answers, follows formats and refuses unsafe requests.
- **Chat template:** instruction-tuned models expect the conversation wrapped in special markers (system, user, assistant). The [[GGUF]] file carries its template, and [[llama.cpp]] applies it.
- **System prompt:** the instructions placed before the user's message. RAG Studio's tells the [[Generator]] to answer only from the numbered passages and to cite them ([[Citations]]).
- **Which to use:** for answering questions, always an instruction-tuned model. Base models are starting points for further training.
- **Embedders and rerankers** are tuned for their own task instead (matching queries with passages), which is why some expect an [[Instruction prefix]].

## Related ideas

- [[Model file names]], [[Reasoning models]]
