# Context window

The most tokens a model can hold at once, counting its instructions, the question, the passages and the answer it writes.

- **Choices for the generator:** 4,096 to 32,768 tokens.
- **Bigger costs memory:** the [[KV cache]] is reserved for the whole window, so a bigger window needs more [[VRAM]] (video random-access memory) even if it is never filled.
- **Too small:** fewer passages fit, because room for the answer is kept first; the lowest-ranked are left out ([[Context budget]]).
- **Measured in:** [[Tokens]].
