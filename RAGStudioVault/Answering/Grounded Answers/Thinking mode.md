# Thinking mode

A setting that lets a model write out its reasoning before the answer: working through the question, weighing the passages, checking itself. It often helps on questions that need several steps, and costs many extra tokens and seconds.

## Reasoning or thinking?

- **The same thing, two names.** "Reasoning" is the capability: a reasoning model is one trained to solve problems step by step ([[Reasoning models]]). "Thinking" is the visible trace it writes, and the mode that switches it on.
- **The vocabulary follows the vendor:** OpenAI says reasoning, Google, Anthropic and Qwen say thinking, DeepSeek says both. llama.cpp's own flags are named `--reasoning` and return the trace as `reasoning_content`, while model templates read a switch called `enable_thinking`.
- **Not the same as "chain of thought" prompting:** asking any model to "think step by step" in the prompt. Thinking mode is trained in, and the trace is kept apart from the answer.

## How it works

- **The chat template decides:** a thinking model's template opens a thinking section before the answer when `enable_thinking` is true, and skips it when false. Models whose template has no such switch ignore it and answer directly ([[Instruction tuning]]).
- **The trace is returned separately:** llama.cpp recognises the model's thinking markers and moves the trace out of the answer, so citations and the answer text stay clean.
- **It shares the output allowance:** thinking tokens count toward the same limit as the answer. A long trace can leave no room for the answer, so the allowance is larger when thinking.

## The cost

- **Time:** every thinking token is generated like an answer token ([[Decoding]]). A trace of 200 tokens at 35 [[Tokens per second]] adds about 6 seconds before the answer starts.
- **In one test in RAG Studio:** "How much do 12 pens cost at 3 for $2?" took 7 tokens and 0.16 seconds without thinking, and 198 tokens and 5.8 seconds with it. The answer was the same.
- **Context:** the trace occupies the [[Context window]] while it is written, alongside the passages.

## When it helps retrieval-augmented generation

- **Helps:** questions that combine several passages, compare, count, or need a calculation. Questions where the passages disagree, or only partly answer.
- **Rarely helps:** looking up one fact that a single passage states. Reading is the hard part there, and that happened in retrieval.
- **A useful check:** reading the trace shows which passages the model weighed and why, a window into how it used the context ([[Grounded Answers]]).

## In RAG Studio

- **Think first,** next to the Ask button, turns thinking on for that question only. No restart is needed.
- **The trace** appears above the answer in a collapsible Thinking section. The token count under the answer includes it.
- **Answers allow 1,024 tokens, plus 3,072 more when thinking,** never more than half the context window ([[Context budget]]).
- **A model without a thinking mode** answers directly, and the page says so.

## Related ideas

- [[Generator]], [[Citations]], [[Retrieval-Augmented Generation]]
