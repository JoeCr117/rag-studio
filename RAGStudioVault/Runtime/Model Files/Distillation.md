# Distillation

Training a small "student" model to imitate a large "teacher" model, so the student keeps much of the teacher's ability at a fraction of the size. Distilled models often carry `Distill` in their names.

- **How it works:** instead of learning only from raw text, the student learns from the teacher's outputs. Those outputs can be its answers, its reasoning traces, or its full probability for every possible next token, which carries more information than the single right word.
- **Why it matters:** the best small models are often distilled. An 8-billion-parameter model trained this way can answer far better than one trained only on text.
- **Reading the name:** `DeepSeek-R1-Distill-Qwen-7B` is a 7-billion-parameter Qwen model taught by DeepSeek's R1 [[Reasoning models|reasoning model]]. The architecture is Qwen's; the behaviour is learned from R1.
- **Not the same as [[Quantization]]:** distillation trains a new, smaller model; quantization stores the same model with fewer bits. The two are often combined.
- **Licences travel:** a distilled model may inherit conditions from both its teacher's and its base model's licences. Check the [[Model card]].

## Related ideas

- [[Parameters]], [[Model file names]]
