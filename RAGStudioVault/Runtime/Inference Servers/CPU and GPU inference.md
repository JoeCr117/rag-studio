# CPU and GPU inference

Running a model on the CPU (central processing unit) with system memory, or on the GPU (graphics processing unit) with its own video memory.

- **GPU:** thousands of small cores and very fast memory, usually many times faster for models, but limited by [[VRAM]] (video random-access memory), 12 GB (gigabytes) on the card RAG Studio is sized for.
- **CPU:** slower, but uses ordinary RAM (random-access memory), of which there is far more, and leaves the GPU free.
- **Choosing:** small embedders and the reranker are fine on the CPU. The [[Generator]] runs on either, but writes answers many times faster on the GPU.
- **CPU only:** without an NVIDIA graphics card and driver, RAG Studio starts CPU-only. It offers no GPU choices and the header says CPU only. Everything works, more slowly.
- **CUDA:** the GPU option uses the CUDA (Compute Unified Device Architecture) build of [[llama.cpp]] for NVIDIA cards.
