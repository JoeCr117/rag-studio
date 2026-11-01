# Citations

Passage numbers in square brackets, such as [2], that the generator writes to show which passages an answer came from.

- **Why:** you can check each claim against the source text, the main way to catch a wrong answer.
- **In RAG Studio:** cited [[Passages]] get a green cited pill and border. Both `[2]` and a list such as `[3, 4, 5]` count, because models differ in how they group citations.
- **Thinking is not checked:** passage numbers mentioned while [[Thinking mode|thinking]] are not citations; only the answer's are.
- **No citations:** often means the passages did not hold the answer; the generator is told to say so instead of guessing.
- **Not proof:** a model can cite a passage that does not support its sentence, so read the cited text.
