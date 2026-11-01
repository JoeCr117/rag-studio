# Generator

The language model that writes the answer on the Ask tab, reading the question and the retrieved passages.

- **Runs on:** the GPU (graphics processing unit) only, through [[llama.cpp]], one model at a time.
- **Choosing one:** bigger models follow instructions and cite more reliably, but need more [[VRAM]] (video random-access memory) and are slower.
- **Settings:** the model and its [[Context window]].
- **Reasoning off:** thinking models run without their hidden reasoning step, so answers come back quickly.
- **Temperature 0.2:** little randomness, so answers stick to the [[Passages]].
