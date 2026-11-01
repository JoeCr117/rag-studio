# Sync status

The state of one source inside one database, shown as a coloured pill: whether the stored chunks still match the files on disk.

- **Synced:** the database matches the files.
- **Changed:** files were added, edited or removed since the last [[Sync]]; Resync brings them in.
- **Not synced:** connected, but nothing has been read yet.
- **Folder missing:** the [[Source]] folder is not on disk; its stored chunks are kept.
- **Disconnected:** the source no longer feeds this database, but its chunks stay until Sync all removes them.
