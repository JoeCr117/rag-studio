# RagStudio

RAG Studio is a local, single-user app that turns folders on the user's own computer into searchable vector databases, then answers questions from them with a local language model. This area describes what it does and how it behaves, without implementation detail, so that the app could be rebuilt from these notes alone.

- **Who uses it:** one person on their own Windows computer, learning how retrieval-augmented generation (RAG) works by building, inspecting and questioning their own databases.
- **Where it runs:** entirely on that computer, in containers, opened as a page in the web browser. Nothing is sent to an online service and nothing needs an account.
- **The target machine:** a desktop with one graphics card holding about 12 gigabytes (GB) of memory. Every model choice and memory warning is sized for that. The card is optional: without one, every model runs on the processor, much more slowly.
- **What makes it different:** it is a teaching tool as much as a tool. Every number the pipeline produces (scores, timings, token counts, vector values, file locations) is shown, and every concept on screen links to a note in this vault.

## Groups

- [[Features]] — what the user can do, one note per capability
- [[Lifecycle]] — how the app starts, how it stops, and what it keeps
- [[Design]] — the principles and moving parts behind the features
