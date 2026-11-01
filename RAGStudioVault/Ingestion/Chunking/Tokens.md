# Tokens

The pieces a language model actually reads and writes: whole words, parts of words, punctuation or spaces, each mapped to a number.

- **Rough size:** in English one token is about three-quarters of a word, so 400 tokens is about 300 words.
- **Each model has its own:** the same sentence can be a different number of tokens for different models, which is why chunk sizes are counted with the embedding model's own [[Tokenizer]].
- **Why they are the unit:** model limits ([[Context window]]), waiting time ([[Prefill]]) and speed ([[Tokens per second]]) are all counted in tokens.
