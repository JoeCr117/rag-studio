# Model file names

A model's file name is a compact label read left to right: who made it and which version, how big it is, what it was trained to do, and how it was shrunk. Learning to read one tells you most of what you need before downloading.

## Reading one, left to right

`gemma-4-26B-A4B-it-UD-Q4_K_M.gguf`

| Part | Meaning |
| --- | --- |
| `gemma-4` | Family and version: Google's Gemma, generation 4 |
| `26B` | 26 billion [[Parameters]] in total |
| `A4B` | About 4 billion **active** per token: a [[Mixture of Experts]] model |
| `it` | Instruction-tuned: trained to follow requests ([[Instruction tuning]]) |
| `UD-Q4_K_M` | Shrunk with the Unsloth Dynamic recipe to about 4.9 bits per weight ([[Quantization]]) |
| `.gguf` | The single-file format llama.cpp loads ([[GGUF]]) |

## More examples from RAG Studio

- `Qwen3-Embedding-0.6B-Q8_0.gguf`: Qwen generation 3, an [[Embedding model]], 0.6 billion parameters, 8-bit.
- `qwen3-reranker-0.6b-q8_0.gguf`: the same family's reranker ([[Cross-encoder]]), with the same size and precision. Letter case carries no meaning.
- `LFM2.5-8B-A1B-Q4_K_M.gguf`: Liquid Foundation Model 2.5, 8 billion parameters with 1 billion active, 4-bit k-quant.
- `granite-4.2-8b-Q5_K_M.gguf`: IBM's Granite 4.2, 8 billion parameters, 5-bit k-quant.
- **Tags are a habit, not a rule:** publishers name files differently, so when a tag is missing, the [[Model card]] says what the model is.

## Other tags you will meet

| Tag | Meaning |
| --- | --- |
| `Instruct`, `it`, `Chat` | Instruction-tuned for conversation |
| `Base`, or no tag on a model family that also ships `Instruct` | Pretrained only: continues text, does not follow requests |
| `Thinking`, `Reasoning`, `R1` | Writes a reasoning trace before answering ([[Reasoning models]]) |
| `Distill` | A smaller model trained to imitate a larger one ([[Distillation]]) |
| `Coder` | Tuned for programming |
| `VL`, `Vision` | Accepts images as well as text (vision-language) |
| `v1.5`, `2507` | Version, or release date (year and month) |
| `128k`, `32k` | Longest supported [[Context window]] |
| `E4B` | "Effective" 4 billion: built to run within the memory of a 4-billion-parameter model although it holds more (Google's Gemma 3n) |

## Repository names

- **The repository** (`owner/name` on [[Hugging Face]]) tells who converted the file, which is not always who made the model.
- **Conversions by others:** `Qwen/Qwen3-Embedding-0.6B-GGUF` is the maker's own conversion; `unsloth/gemma-4-12b-it-GGUF` is a third party's.
- **The `-GGUF` suffix** marks a repository of converted files. Usually each quantization level is a separate file in it, so choose the file, not just the repository.
