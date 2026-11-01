# Quantization

Storing a model's weights with fewer bits each, such as 8 or 4 instead of 16, to make it smaller and faster at a small cost in accuracy.

- **Why it matters here:** a 9-billion-parameter model is about 18 GB (gigabytes) at 16 bits but about 5.5 GB at Q4_K_M, which fits in 12 GB of [[VRAM]] (video random-access memory). See [[Parameters]] for the arithmetic.
- **Speed:** writing each token reads every active weight once, so smaller weights mean faster [[Decoding]].
- **What is lost:** each weight is rounded to one of a few levels. At 8 bits the difference is hard to measure; at 4 to 5 bits it is small; below 3 bits answers get noticeably worse.
- **Where it shows in a name:** the last part of a [[Model file names|model file name]], such as `Q4_K_M`.

## Reading the label

| Part | Meaning |
| --- | --- |
| `Q` + number | Roughly how many bits each weight keeps (`Q4` ≈ 4, `Q8` ≈ 8) |
| `_0`, `_1` | The original "legacy" schemes: weights in blocks of 32, each block with one scale (`_0`) or a scale and an offset (`_1`) |
| `_K` | A k-quant: blocks grouped into super-blocks of 256 weights, with the scales themselves quantized, so precision goes where it is needed |
| `_S`, `_M`, `_L` | Small, medium, large: how many of the most sensitive parts (such as attention values and some feed-forward weights) are kept at a higher precision |
| `IQ` | An i-quant: weights are matched to entries in a precomputed codebook, which keeps quality at very low bit counts (`IQ2`, `IQ3`) but runs slower on a CPU (central processing unit) |
| `XS`, `XXS`, `NL` | i-quant sizes (extra small, extra-extra small) and a non-linear variant |
| `F16`, `BF16`, `F32` | Not quantized: 16- or 32-bit [[Floating-point precision]] |
| `UD-` | Unsloth Dynamic: a publisher's recipe that picks a precision per layer, as in `UD-Q4_K_M` |

## Bits per weight

Approximate averages. Exact figures vary by model, because each scheme mixes precisions across layers.

| Label | Bits per weight | Size of an 8-billion-parameter model |
| --- | --- | --- |
| F16 / BF16 | 16 | 16 GB |
| Q8_0 | 8.5 | 8.5 GB |
| Q6_K | 6.6 | 6.6 GB |
| Q5_K_M | 5.7 | 5.7 GB |
| Q4_K_M | 4.9 | 4.9 GB |
| Q4_K_S | 4.6 | 4.6 GB |
| IQ4_XS | 4.3 | 4.3 GB |
| Q3_K_M | 3.9 | 3.9 GB |
| IQ2_XS | 2.3 | 2.3 GB |

## Importance matrix

- **What it is:** a table of which weights matter most, measured by running sample text through the full-precision model.
- **What it does:** quantization spends its precision on those weights. Low-bit i-quants depend on it.
- **How to tell:** files made with one are often marked `imatrix` or `imat` in the repository's description.

## Choosing one

- **Q8_0** for small models (embedders, rerankers), where the size saving is tiny and accuracy matters most.
- **Q4_K_M or Q5_K_M** for generators: the usual balance of size and quality.
- **Below Q4,** only when nothing larger fits. A bigger model at Q3 often still beats a smaller model at Q8.
- **In RAG Studio:**
  - the reranker and most embedders are Q8_0; the 4-billion-parameter embedder is Q4_K_M;
  - generators are Q4_K_M or Q5_K_M, sized for 12 GB.
