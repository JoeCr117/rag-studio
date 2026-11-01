# Floating-point precision

How many bits a computer uses to store each number, and how it splits them between range (how large or small a number can be) and detail (how many significant digits it keeps). Models are trained in 16 or 32 bits; [[Quantization]] goes lower.

| Format | Bits | Range and detail | Used for |
| --- | --- | --- | --- |
| F32 (single precision) | 32 | Wide range, about 7 significant digits | Older training, some sensitive layers |
| F16 (half precision) | 16 | Narrow range, about 3 significant digits | Running models on graphics cards |
| BF16 (brain floating point) | 16 | The same range as F32, about 2 significant digits | Training today; Google's design, named after Google Brain |
| F8 / FP8 | 8 | Very narrow | Newest training and serving hardware |

- **Why BF16 won training:** values during training can be tiny or huge. BF16 keeps F32's range and gives up detail, which training tolerates. F16 overflows instead.
- **Why it matters when downloading:** an `F16` or `BF16` file is the unquantized original. It is twice the size of `Q8_0` and is a source to quantize from, not usually a file to run on a 12 GB (gigabyte) card.
- **In RAG Studio:** stored vectors use 32-bit floats, or 16-bit "half" floats above 2,000 [[Dimensions]] ([[halfvec]]). The [[KV cache]] is kept at 8 bits.

## Related ideas

- [[Parameters]], [[Model file names]]
