# Sync

Making a database's stored chunks match the files in its sources: new files are added, edited files re-embedded and deleted files removed.

- **Change detection:** each file's path, size and modified time are compared with the listing at the last sync. That tells whether a source needs syncing, without reading any file.
- **[[Content hash]]:** during a sync every file is read and fingerprinted. Only files whose fingerprint changed are chunked and embedded, so a file whose timestamp moved but whose text did not is never embedded twice.
- **Progress:** a bar on the database, source and job shows the file being worked on and how many of the source's files are done.
- **Sync:** one source into one database, or, from the source's card, into every running database it feeds.
- **Sync all:** every connected source of one database, plus removing the chunks of disconnected sources and a [[Rebuild]] if the vector settings changed.
- **Needs the database running:** syncing calls its [[Embedder]] to turn new chunks into [[Embeddings|vectors]].
- **Runs as a job:** see [[Jobs]].
