# Context budget

How the generator's context window is shared out before it answers: room is kept for the answer first, and the passages fill what is left, best first, until the next one would not fit.

- **Why it is needed:** the window holds the prompt and the answer together. Fill it with passages and the model stops when the window is full, mid-sentence, with no error.
- **The answer's share:** 1,024 [[Tokens]], or 4,096 with [[Thinking mode]], but never more than half the [[Context window]].
- **The passages' share:** everything else. The prompt is counted with the generator's own chat template and tokenizer, so the count is exact rather than a guess from word counts.
- **What gets left out:** the lowest-ranked passages, because search already ordered them best first ([[Passages]]). The answer card says how many were left out.
- **The trade-off:** more passages give the model more evidence but cost [[Prefill]] time; a larger window holds more but reserves more [[VRAM]] (video random-access memory) for the [[KV cache]].
- **Cut-off answers:** an answer that still runs out of its share is flagged as cut off, so a half answer is never mistaken for a whole one.
