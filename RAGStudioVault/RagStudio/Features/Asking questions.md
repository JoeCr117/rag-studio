# Asking questions

The Ask tab is retrieval-augmented generation (RAG) end to end: it finds the best passages for a question, gives them to a local language model, and shows an answer that cites the passages it used. See [[Retrieval-Augmented Generation]].

## What the user can do

- **Run the generator:** pick a model from a curated list of open models that fit the graphics card, pick a [[Context window]] (4,096 to 32,768 tokens) and whether it runs on the central processing unit (CPU) or the graphics processing unit (GPU), then Start, Switch to another choice, or Stop. Each option shows its estimated memory need for the chosen context: graphics memory on the GPU, system memory on the CPU.
- **Run the reranker:** pick its model and whether it runs on the CPU or the GPU, then Start, Switch or Stop.
- **Ask:** pick a database, then use the same mode, result-count and rerank controls as [[Finding passages]], and type a question. Enter asks; Shift+Enter starts a new line.
- **Think first:** tick it to let the generator reason before answering, for that question only ([[Thinking mode]]).

## How it behaves

- **There is one generator and one reranker at a time,** shared by every database. Each card shows its status (running, starting/stopping, stopped) and its memory use.
- **Both can run on either,** and the GPU is much faster; a generator on the CPU takes many times longer per answer. Each card starts on the runtime it last used, or the GPU when there is one. Without a graphics card only the CPU is offered.
- **Starting either one** downloads its model first if needed, with a progress bar on the card, goes through the [[GPU memory guard]], and waits until the model server answers. A start that never becomes healthy is cleaned up, so it does not keep holding memory.
- **Asking retrieves first, then fits the passages to the window:** room for the answer is kept, and the passages fill the rest, best first. Passages that do not fit are left out, and the page says how many ([[Context budget]]).
- **The passages that fit** are numbered [1], [2], … and given to the [[Generator]] with an instruction:
  - answer only from these passages;
  - cite them by number;
  - say "I do not know" when they do not contain the answer;
  - be concise.
- **The answer is formatted:** lists, bold text, code and tables in the model's reply appear as such, not as raw markup symbols. Images in a reply are never shown.
- **The answer card** shows the answer, three timing badges (how long reading the prompt took ([[Prefill]]), how long writing the answer took ([[Decoding]]), and [[Tokens per second]]), and how many of the passages found fit the window.
- **Below it, the passages the generator received** are listed with all their scores. The ones the answer cited are highlighted ([[Citations]], [[Passages]]).

- **Thinking, when ticked:**
  - The generator is told per question whether to think, so one running generator serves both kinds of question, with no restart.
  - Its reasoning comes back separately from the answer and appears above it in a collapsible Thinking section, with its length in words.
  - The token count says it includes thinking.
  - The output allowance grows from 1,024 to 4,096 tokens, because thinking and answer share it, but never past half the context window.

## Edge cases

- **A model without a thinking mode** ignores the switch and answers directly; the page says no thinking came back.
- **An answer that runs out of its allowance** is marked as cut off, so a partial answer never looks complete.
- **A question too long to leave room for any passage** is refused with the token counts.
- **A model server that refuses a request or has stopped** is reported with its own explanation, not a generic server error.
- **Thinking that uses the whole allowance** leaves no answer; the page says so and suggests asking again or turning thinking off.

- **The Ask button is disabled with a reason** when the database is stopped or the generator is not running.
- **Reranking is skipped, not failed,** when the reranker is not running; the tick box says why.

## Related ideas

- [[Grounded Answers]], [[Generation Speed]], [[Mixture of Experts]], [[Quantization]]
