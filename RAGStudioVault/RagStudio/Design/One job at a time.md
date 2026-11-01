# One job at a time

Slow work in RAG Studio is queued as a job and run one at a time, oldest first, while the interface stays responsive. Two jobs never compete for the graphics card, the disk or the same database.

- **Jobs:**
  - creating, starting, stopping, syncing and deleting a database;
  - downloading a model;
  - starting and stopping the generator or reranker.
- **Not jobs:** reading state, browsing, querying and asking. These answer straight away.
- **A database job cannot be queued twice:** pressing the same button for the same database while that job is still waiting returns the waiting job.
- **Every job ends with a result or an error,** in the job list and the terminal ([[Activity log]]). An expected refusal reads as a plain sentence: "start it first", "needs a rebuild".
- **Work that would be wrong is refused, not attempted:** syncing a stopped database, a single-source sync on a database that needs a rebuild, deleting a model while any job is waiting.
- **Shutdown cancels what is waiting,** and the next start marks an interrupted job failed, so the queue never shows a job stuck as running.

## Related ideas

- [[Jobs]], [[App components]]
