# Chunk size

The smallest and largest number of tokens a chunk may hold; the splitter fills each chunk toward the maximum without breaking text mid-sentence.

- **Min tokens:** a chunk is only cut once it holds at least this much, which avoids tiny fragments such as a lone heading.
- **Max tokens:** the hard upper limit. It must stay under what the embedding model reads in one go, 2,048 tokens here.
- **Small chunks (about 150 to 300):** precise matches, but each carries little context.
- **Large chunks (about 800 to 1,024):** more context per hit, but the vector averages more topics, so matches get vaguer, and each [[Passages|passage]] fills more of the [[Context window]].
- **Default:** 150 to 400 tokens.
- **Changing it:** alters every vector, so the database needs a [[Rebuild]].
- **Counted by:** the embedding model's own [[Tokenizer]], in its [[Tokens]].
