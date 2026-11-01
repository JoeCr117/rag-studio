# Reasoning models

Models trained to write out a chain of reasoning, often called thinking, before their final answer. They solve harder problems this way, but spend many extra tokens and seconds doing it.

- **How it looks:** the model first writes its working, usually between markers such as `<think>` and `</think>`, then the answer. Interfaces typically hide the working.
- **Hybrid models** can switch thinking on or off per request, Qwen3 and Qwen3.5 among them. The model server or a flag in the prompt decides.
- **The cost:** the reasoning trace can be hundreds or thousands of tokens. At 50 [[Tokens per second]], a thousand-token trace adds 20 seconds before the answer starts. The trace also fills the [[Context window]].
- **When it helps:** multi-step math, logic, planning, code. Retrieval-augmented generation (RAG) mostly needs reading and summarising the retrieved passages, where thinking adds time more than accuracy.
- **In RAG Studio:** thinking is off unless Think first is ticked for a question ([[Thinking mode]]).
- **Reasoning versus thinking:** two names for the same thing. Reasoning is the capability, and thinking is the trace and the mode that turns it on.
- **Name tags:** `Thinking`, `Reasoning`, `R1` ([[Model file names]]).

## Related ideas

- [[Instruction tuning]], [[Generator]], [[Decoding]]
