# Keeping databases current

Sources and databases are connected many-to-many, and RAG Studio always knows whether each source's content in each database still matches the files on disk. Syncing makes them match again, doing only the work that changed.

## What the user can do

- **Connect** a source to a database, from either side (the source's or the database's drop-down).
- **Sync one source into one database,** or a source into every database it feeds.
- **Sync all** in a database: every connected source, plus clean-up and rebuild.
- **Disconnect** a source from a database, and **Reconnect** it before its chunks are removed.

## How it behaves

- **Every connection has a status,** shown as a badge on both the source and the database ([[Sync status]]):
  - **Synced:** the files have not changed since the last sync.
  - **Changed:** something was added, edited or removed since then.
  - **Never synced:** connected, not yet synced.
  - **Folder missing:** the folder cannot be found.
  - **Disconnected:** its chunks are still stored but waiting for removal.
- **Change detection is cheap:** it compares file listings (path, size, modified time), not file contents, so it can run constantly.
- **A sync is precise:**
  - Each file's content is fingerprinted. Unchanged files are skipped, changed files are re-chunked and re-embedded, and files no longer present are removed from the database.
  - The result reads as counts: added, updated, unchanged, removed, chunks embedded.
  - Each file's change also appears in the [[Activity log]].
- **A sync shows its progress** on the database's card, the source's row and the job list. Each bar shows:
  - how many of the source's files are done, and the percentage;
  - the file being worked on, prefixed by its source name. Sync all adds "2 of 3" to the source name.
  - Steps without a count, such as emptying the database for a rebuild or removing a disconnected source, show a moving bar with what is happening.

  The bar races through unchanged files and slows on files being embedded. Its popup explains why ([[Content hash]]).
- **A sync waiting behind another job** says "Waiting in the queue" with its title, instead of looking idle.
- **Chunking follows the file type:** Markdown is split along its headings, everything else along paragraphs and lines. Chunks are measured in the embedding model's own tokens ([[Tokenizer]]), within the database's minimum, maximum and overlap.
- **Each chunk is embedded with a short header** naming its file and source, so a chunk from the middle of a file still says where it came from ([[File header]]). Models that expect task prefixes on documents and queries get them ([[Instruction prefix]]).
- **The database shows warnings** in the order to act on them: settings changed (needs rebuild), a disconnected source still has chunks, some sources are not synced. The Sync all button is highlighted while any warning stands.
- **Sync all does three things in order:** rebuilds from empty if the settings changed, removes the chunks of disconnected sources (and their connections), then syncs every connected source.

## Edge cases

- **Syncing needs the database running,** because the embedder must be loaded; the buttons are disabled and explain why otherwise.
- **A database that needs a rebuild refuses single-source syncs.** Only Sync all may rebuild, so a database never mixes vectors made with different settings.
- **A missing folder refuses to sync** and keeps its old chunks, rather than treating every file as deleted.

## Related ideas

- [[Sync]], [[Chunking]], [[Embeddings]], [[Document]]
