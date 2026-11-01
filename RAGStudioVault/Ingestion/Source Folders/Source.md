# Source

A folder on this machine that RAG Studio reads files from to build its databases.

- **Read-only:** RAG Studio never changes, moves or deletes anything in a source.
- **How it is read:** the worker container sees every drive through one read-only [[Host drives mount]], so a source is just a path inside it.
- **Scanned every second:** the worker lists the files that match the source's [[File patterns]] and notices additions, edits and deletions.
- **Feeds databases:** one source can feed several databases, and one database can read several sources. Each pairing has its own [[Sync status]].
- **Missing folder:** if the folder is moved, deleted or its drive is unplugged, the source shows Folder missing and its stored chunks stay until it returns.
