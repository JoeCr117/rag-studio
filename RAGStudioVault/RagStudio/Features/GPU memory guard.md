# GPU memory guard

Before RAG Studio loads any model onto the graphics processing unit (GPU), it estimates the memory the model needs and warns when that would not fit. When a model overflows the card's memory, everything slows to a crawl instead of failing cleanly.

## What the user can do

- **Watch the card's memory** in the header at all times: used and total for the whole card, including other programs' use.
- **Choose at a warning:** Cancel, or **Start anyway**.

## How it behaves

- **Every GPU start goes through the same check:** embedders, the generator and the reranker.
- **The estimate is per model:**
  - its weights plus working buffers;
  - for generators, plus the [[KV cache]] for the chosen [[Context window]].
- **The check counts what the start will free.** Switching the generator or reranker replaces the running one, so its memory counts as available. A GPU embedder already running for another database needs nothing new.
- **Headroom is kept:** the estimate is compared with free memory minus 1 gigabyte (GB). Near the card's limit, the graphics driver spills into system memory and speed collapses ([[VRAM]]).
- **A shortfall does not refuse the start;** it asks. The warning appears as a banner naming the need and the free memory, with Start anyway and Cancel.
- **After every GPU start, the real use is measured** and reported next to the estimate in the job's result, so the user learns how good the estimates are.
- **Starting on the central processing unit (CPU) skips the check.**
- **Without a graphics card there is nothing to guard:** the header shows CPU only, and GPU choices are not offered ([[Starting the app]]).

## Related ideas

- [[VRAM check]], [[GPU Memory]], [[CPU and GPU inference]]
