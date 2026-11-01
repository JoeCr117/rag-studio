# Database management

A vector database in RAG Studio is a named collection of chunks and their vectors, built with one fixed combination of engine, embedding model and chunking settings. The user can make as many as they like, to compare how those choices change the results.

## What the user can do

- **Create a database** with a name and these settings, each picked from a short list rather than typed:
  - **Engine:** one of two interchangeable [[Vector engine]]s, a vector extension inside a relational database ([[pgvector]]) and a dedicated vector database ([[Qdrant]]).
  - **[[Embedding model]]:** a curated list of small open models with different [[Dimensions]], languages and sizes. Each option says whether it is downloaded yet and how large it is.
  - **Embedder runs on:** the central processing unit (CPU) or the graphics processing unit (GPU). See [[CPU and GPU inference]]. Only the CPU is offered when the app started without a graphics card.
  - **Default query mode:** hybrid (vector plus keyword) or vector only.
  - **Chunk minimum, maximum and overlap,** in tokens. See [[Chunk size]] and [[Chunk overlap]].
- **Start and stop it.** Starting loads its embedding model into a model server (its [[Embedder]]); a stopped database can be browsed but not synced or queried.
- **Edit its settings** at any time.
- **Delete it** after a confirmation step.

## How it behaves

- **Each database card shows** its name, Running/Stopped and Creating…/Working… badges, every setting as a short line, its document and chunk counts, and its warnings. A table lists its connected sources, each with a status badge and Sync, Resync, Disconnect or Reconnect buttons.
- **Creating and deleting are queued jobs** (see [[One job at a time]]), so the card says Creating… until the empty database exists.
- **The card shows what its job is doing:**
  - a progress bar while one of its jobs runs: files for a sync, bytes while starting downloads the model;
  - a moving bar for steps that cannot count, such as waiting for the embedder to load;
  - "Waiting in the queue" while its job waits behind others.
- **Embedders are shared.** Two running databases with the same model on the same hardware use one model server. Stopping a database stops its embedder only when no other running database still uses it.
- **Starting downloads the model first if needed,** and on the GPU goes through the [[GPU memory guard]].
- **Vectors too wide for a normal index** are stored at half precision, so every model in the list can be indexed. See [[halfvec]] and [[HNSW index]].
- **Changing a setting that alters the vectors** (engine, model or chunking) shows a warning in the form before saving. Once saved, the database is marked as needing a [[Rebuild]]; the next Sync all empties and rebuilds it.
- **Changing the model or its hardware is refused while the database is running,** because the running embedder would no longer match.
- **Deleting** stops its embedder if nothing else uses it, then removes the whole database from its engine, along with its connections to sources.

## Related ideas

- [[Vector Databases]], [[Keeping databases current]]
