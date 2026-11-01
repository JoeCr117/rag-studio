# Parameters

The numbers a model learned during training, also called weights. A model's size is counted in parameters, such as 8B for 8 billion, and that count decides how much memory the model needs and roughly how capable it is.

- **What they are:** the strengths of the connections between a neural network's units. Training adjusts them until the model's predictions match its training text.
- **Memory:** parameters × bits per weight ÷ 8 = bytes.
  - 8 billion at 16 bits is 16 GB (gigabytes).
  - At 4.9 bits ([[Quantization]] `Q4_K_M`) it is about 4.9 GB.
  - Running it also needs working memory, mostly the [[KV cache]].
- **Capability:** more parameters usually means more knowledge and better reasoning, but training data and method matter as much. A recent 8-billion-parameter model can beat an older 70-billion-parameter one.
- **Speed:** writing each token touches every active parameter once, so fewer active parameters means faster [[Decoding]]. That is why [[Mixture of Experts]] models count total and active parameters separately.
- **In RAG Studio:**
  - embedders and the reranker are about 0.14 to 4 billion parameters, mostly small enough for the CPU (central processing unit);
  - generators are 8 to 26 billion, which need the graphics card.

## Related ideas

- [[Model file names]], [[VRAM]]
