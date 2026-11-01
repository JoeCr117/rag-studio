# VRAM

Video random-access memory: the graphics card's own memory, which must hold a model's weights and working data for it to run on the GPU (graphics processing unit).

- **Target size:** RAG Studio's model choices and estimates are sized for a 12 GB (gigabyte) card; other apps on the desktop use some too.
- **What fills it:** model weights, the [[KV cache]] and working buffers.
- **When it runs out:** on Windows the driver quietly spills into system memory and speed collapses, instead of failing with an error.
- **The meter:** the header shows how much the whole card is using, by every program.
- **Guarded by:** the [[VRAM check]].
