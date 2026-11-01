# Folders stay untouched

RAG Studio only ever reads the user's folders, in place. It never writes to them, never copies them, and never lets a missing folder stop anything else from working.

- **Read-only by construction:** the containers see the computer's drives through a view that cannot write, so not even a bug could change a file.
- **No copies:** files are read when a sync needs them. Only the chunks and vectors made from them are stored, and only inside a database.
- **Registering a folder changes nothing about how the app is set up.** No restart is needed, and no list of folders has to exist for the app to start.
- **A missing folder is a status, not an error:** the source shows Folder missing, its chunks are kept, syncing it waits, and it is picked up again when it returns.
- **Deleting a source's chunks is always explicit:** the user disconnects it and runs Sync all. A missing folder is never taken to mean its files were deleted.

## Related ideas

- [[Folder sources]], [[Host drives mount]], [[Kept and removed]]
