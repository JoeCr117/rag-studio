# Content hash

A short fingerprint computed from a file's exact bytes: the same content always gives the same fingerprint, and any change gives a different one. Syncing compares fingerprints to decide which files need embedding again.

- **Why it matters:** embedding is the slow, expensive step. Reading a file and computing its fingerprint is fast, so a sync can check every file and embed only the ones whose content really changed.
- **How it works:** RAG Studio stores each file's fingerprint (a SHA-256, Secure Hash Algorithm with 256 bits, written as 64 hexadecimal characters) next to its chunks. The next sync reads each file, computes its fingerprint and compares: same means skip, different means re-chunk and re-embed.
- **Why it is not just the modified time:** saving a file without changes, copying it, or syncing a cloud folder can change its timestamp but not its content. The timestamp is enough to notice that something *might* have changed ([[Sync status]]); the fingerprint confirms it.
- **What it looks like in RAG Studio:** the sync progress bar counts every file, but races through unchanged files and slows down on files that are being embedded.

## Related ideas

- [[Sync]], [[Embeddings]], [[Document]]
