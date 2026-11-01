# llama.cpp

An open-source program that runs language models from GGUF files on the CPU (central processing unit) or GPU (graphics processing unit) and answers requests over HTTP (Hypertext Transfer Protocol).

- **In RAG Studio:** every model runs in a llama.cpp server container: each [[Embedder]], the [[Generator]] and the reranker ([[Cross-encoder]]).
- **Two builds:** one for the CPU and one using CUDA (Compute Unified Device Architecture) for NVIDIA graphics cards.
- **A pinned version:** llama.cpp publishes a numbered build almost daily, such as b12019, and options are sometimes renamed between builds. RAG Studio names one tested build instead of "latest", so an update never silently breaks the options it passes, such as turning thinking on or off. Moving to a newer build is a deliberate change, tested by starting each kind of server.
- **Started on demand:** by the control service, and removed by Shut down.
- **Models mounted read-only:** from the models [[Docker volume]].
