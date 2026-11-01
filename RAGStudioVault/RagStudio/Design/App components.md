# App components

RAG Studio is a handful of cooperating parts, each with one responsibility. All but one run as containers on the user's computer, and they talk to each other over local network connections.

## The parts

| Part | Responsibility |
| --- | --- |
| Page | The single-page interface in the browser. It polls the app's state about once a second and sends the user's actions. |
| Application programming interface (API) | Answers the page: validates requests, reads state, queues jobs, and answers queries and questions directly. It also streams log lines. |
| Worker | Watches every source folder about once a second, and runs queued jobs one at a time. |
| Controller | The only part allowed to start and stop containers. It offers a short list of fixed actions ([[Least privilege]]). |
| Metadata store | A relational database holding the app's own records: sources, databases, connections, jobs, log lines, server settings. |
| Two vector engines | A vector extension inside a relational database ([[pgvector]]) and a dedicated vector database ([[Qdrant]]). Each app database is one database or collection inside one of them. |
| Model servers | Started on demand from local model files ([[llama.cpp]]): one embedder per embedding model and hardware choice, shared by databases, plus one generator and one reranker. Always one fixed, tested version, because the app relies on its options. |
| Folder dialog helper | The one part that runs on Windows itself, outside containers. It opens the operating system's folder dialog for Browse…, because a container cannot open a window and a web page is never told a folder's full path. |

## How they fit

- **Every vector engine fulfils the same contract** ([[Vector engine]]):
  - create, drop and count;
  - replace a document's chunks, remove documents, remove a source;
  - list stored documents and chunks;
  - query by vector or hybrid.

  Adding a third engine means implementing that contract, nothing else.
- **Hybrid queries fuse rankings the same way in every engine,** so results can be compared across engines.
- **Source folders are reached through one read-only view of every drive,** given only to the worker. Registering a folder never changes how the containers are set up ([[Host drives mount]]).
- **Models live in one shared volume.** The model servers read it without being able to change it.
- **The page never talks to containers directly,** only to the API and, for Browse…, to the folder dialog helper.

## Related ideas

- [[Starting the app]], [[One job at a time]], [[Docker Storage]], [[Inference Servers]]
