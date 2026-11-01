# Host drives mount

One fixed, read-only window from the worker container onto every Windows drive, through which RAG Studio reads source folders.

- **Path inside the container:** /host, then the drive letter, then the rest of the path, so W:\Notes becomes /host/w/Notes.
- **Why one mount:** Docker checks every mount when a container starts. Mounting each source separately would let one deleted folder stop the whole app.
- **Read-only:** the worker can read any file but change none.
- **Missing folders:** show as Folder missing on the [[Source]] instead of failing.
- **Local drives only:** Docker Desktop shares the PC's own drives, internal or USB, and nothing else.
  - A network share (`\\server\share`) is refused when registering a source.
  - A network drive mapped to a letter is not visible inside Docker at all.
  - Copy such a folder to a local drive first.
- **Drives plugged in later** appear without a restart.
