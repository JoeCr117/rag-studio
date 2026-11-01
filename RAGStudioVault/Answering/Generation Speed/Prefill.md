# Prefill

The first phase of generating an answer: the model reads the whole prompt, meaning the instructions, question and passages, before it can write the first word.

- **Shown as:** prefill, then the tokens read and the time taken, after each answer.
- **Fast per token:** prompt tokens are processed in parallel, so prefill runs at hundreds to thousands of tokens per second on a GPU (graphics processing unit).
- **Grows with passages:** more or larger [[Passages]] mean a longer wait before the answer starts.
- **Also called:** prompt processing.
