# Tokens per second

How many answer tokens the generator writes each second while decoding; the green tok/s pill after each answer.

- **Reading it:** 4 tokens are about 3 words, so 40 tokens per second is roughly 30 words per second, far faster than reading speed.
- **What lowers it:** a larger model, a model that does not fit in [[VRAM]] (video random-access memory), or experts kept in system memory ([[Mixture of Experts]]).
- **Measures:** [[Decoding]] only, not [[Prefill]].
