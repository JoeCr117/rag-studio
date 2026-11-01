# Embedder

The running server that turns text into vectors for one embedding model; starting a database starts its embedder.

- **Shared:** databases with the same [[Embedding model]] and runtime use the same embedder container.
- **Needed for:** [[Sync]], to embed chunks, and every search, to embed the question.
- **Running and Stopped:** a database's status pill shows whether its embedder is up. Stopping the last database that uses one removes it.
- **Runs on:** the CPU (central processing unit) or GPU (graphics processing unit); see [[CPU and GPU inference]].
