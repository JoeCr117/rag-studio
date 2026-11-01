# Model card

The description page published with a model, shown as the front page of its [[Hugging Face]] repository. It says what the model is for, how it was trained, how to prompt it, how well it scores, and under what licence it may be used.

- **Read it for:**
  - **Intended use:** chat, embedding, reranking, code; and what it is not meant for.
  - **Prompt format:** chat template, [[Instruction prefix]]es for embedders, whether thinking can be switched off ([[Reasoning models]]).
  - **Context length:** the longest input it was trained for ([[Context window]]).
  - **Benchmarks:** scores on standard tests. Useful for comparing, but every publisher picks the tests that flatter them.
  - **Licence:** some permit any use; others restrict commercial use, require attribution, or need you to accept terms before downloading (a "gated" model).
- **Converted copies:** a `-GGUF` repository's card usually lists each quantization file with its size, and links back to the original model's card for everything else ([[Model file names]]).
- **In RAG Studio:** every model on the Models tab links to its repository, so its card is one click away. Only models that download without accepting terms are offered.

## Related ideas

- [[GGUF]], [[Quantization]]
