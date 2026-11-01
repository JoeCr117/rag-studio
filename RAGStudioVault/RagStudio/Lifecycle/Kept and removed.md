# Kept and removed

What RAG Studio keeps between runs, and how completely deleting something removes it. The user's own folders are never changed. Everything the app makes lives in containers and data volumes it owns.

## Kept across shutdown and restart

- **Data volumes:** these survive shutdowns, rebuilds and image deletion. Removing a volume itself is the only way to lose them.
  - the two vector engines' data;
  - downloaded models;
  - the app's own records: sources, databases, connections, settings, jobs and logs.
- **Container images:** programs only, never user data.

## Removed by deleting

- **A database:** the whole database is dropped from its engine, its connections to sources go with it, and its embedder stops if nothing else uses it. Its chunks and vectors are gone.
- **A source:** unregistering is only allowed once no database holds its chunks (disconnect it and use Sync all first). So when a source is gone, no copy of its content remains anywhere. The app never copied the files themselves; it only ever read them in place.
- **A model:** its file, its download records and its cached tokenizer are deleted. The next start downloads it again.

## Removed automatically

- **Partial downloads:**
  - a model download cut short by a stop or crash cannot be resumed, so its next attempt starts from zero;
  - the partial file would otherwise stay forever, invisible in the interface;
  - the app deletes every partial download each time it starts, because nothing can be downloading at that moment.

## What deleting leaves behind

- **Log lines** that mention the deleted thing: names, folder and file paths, and the first words of searches. These roll off as the log is trimmed to its newest 5,000 lines. File text and answers are never logged.
- **Job history:** entries like "Sync 'Notes' into 'Research'" stay, with their link to the deleted item cleared. These are not trimmed.
- **Engine write-ahead logs:** a relational database records each change in a write-ahead log before applying it, for crash safety. Recent chunks can linger there briefly after a drop, until the engine reuses that space.
- **Freed disk space is not wiped:** deleting marks space as free inside the container engine's virtual disk. That disk is one large file on Windows and does not necessarily shrink on its own; the container engine's disk clean-up compacts it.

## Related ideas

- [[Docker volume]], [[Docker image]], [[Model library]], [[Shutting down the app]]
