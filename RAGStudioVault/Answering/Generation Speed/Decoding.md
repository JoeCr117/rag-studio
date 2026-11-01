# Decoding

The second phase of generating an answer: the model writes the reply one token at a time, each new token depending on all the ones before it.

- **Shown as:** generated, then the tokens written and the time taken.
- **Slower per token than [[Prefill]]:** tokens cannot be computed in parallel, and each one reads the model's weights from memory again.
- **Limited by memory speed:** how fast the GPU (graphics processing unit) can read the weights sets the pace, which is why smaller or [[Quantization|quantized]] models write faster.
- **Measured as:** [[Tokens per second]].
