# GGUF

GGUF, the GPT-Generated Unified Format (GPT: Generative Pre-trained Transformer), is a single file holding a model's weights, tokenizer and settings, ready for llama.cpp to load.

- **One file per model:** easy to download, copy and delete. RAG Studio keeps them in the models [[Docker volume]].
- **Usually quantized:** the weights are stored at reduced precision, and the label says how (see [[Quantization]]).
- **Loaded by:** [[llama.cpp]].
- **Downloaded from:** [[Hugging Face]].
