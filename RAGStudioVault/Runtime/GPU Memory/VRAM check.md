# VRAM check

Before starting any model on the GPU (graphics processing unit), RAG Studio estimates its memory need and warns when less than 1 GB (gigabyte) of video memory would be left free.

- **Why 1 GB of headroom:** near the limit, Windows spills into system memory and everything on the GPU slows down.
- **The warning:** a yellow banner with Start anyway; you can stop something first instead.
- **Estimates:** come from the model catalog; after each start the job reports measured against estimated use.
- **Applies to:** embedders, the [[Generator]] and the reranker. See [[VRAM]].
