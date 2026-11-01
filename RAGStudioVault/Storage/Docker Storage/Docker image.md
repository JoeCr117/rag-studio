# Docker image

A read-only package of a program and everything it needs to run; a container is a running copy of an image.

- **RAG Studio's own images:** backend (the api and worker), web and control, rebuilt by start.ps1 when Build is chosen.
- **Downloaded images:** pgvector, Qdrant and [[llama.cpp]].
- **Built-in models:** [[BM25]] lives inside the Qdrant image and Postgres [[Full-text search]] inside the pgvector image, so they need no download.
- **No downloaded models inside:** [[GGUF]] files live in a [[Docker volume]], so rebuilding an image never downloads them again.
