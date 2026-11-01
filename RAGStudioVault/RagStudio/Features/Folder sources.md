# Folder sources

A source is a folder on the user's computer that RAG Studio reads files from. The user registers it once, and can then feed it into any number of vector databases.

## What the user can do

- **Register a folder** by typing its path or pressing **Browse…**, which opens the operating system's own folder dialog (not an imitation drawn inside the page). Choosing a folder fills in its full path; cancelling leaves the field unchanged. The dialog opens at the typed folder when that folder exists.
- **Name it,** or leave the name empty to use the folder's own name.
- **Choose which files count** with [[File patterns]]: an include list and an exclude list, one pattern per line, in the same syntax as a `.gitignore` file. These can be set when registering and edited later.
- **See its state at a glance:** a live count of the files that qualify, or a **Folder missing** warning.
- **Sync it** into every database it is connected to with one button, which reads **Resync** when any of them is out of date. While one of its syncs runs, its row shows a progress bar with the file being worked on.
- **Connect it** to a database from a drop-down list of databases it does not feed yet.
- **Unregister it** after a confirmation step.

## How it behaves

- **Registering checks the path is really reachable** before saving, and refuses duplicates by path (ignoring letter case) and by name.
- **Default includes:** Markdown, plain text and common source-code and config file types. An empty include list means these defaults.
- **Always skipped:** version-control, dependency, build, editor and note-app folders (for example `.git`, `node_modules`, `.venv`, `.obsidian`). Also skipped: anything a `.gitignore` inside the folder ignores, and files over 2 megabytes.
- **The folder is watched,** not copied. The file listing (path, size, modified time) is re-read about once a second, so the count and the [[Sync status]] of every database it feeds stay current without the user doing anything.
- **Nothing is ever written to the folder.** See [[Folders stay untouched]].

## Edge cases

- **Network folders cannot be sources:** only the computer's local drives (internal or USB) are readable.
  - A network path is refused at once, with that reason.
  - A network drive mapped to a letter fails the reachability check.
- **Folder moved, deleted or its drive unplugged:** the source shows **Folder missing**, its stored chunks stay in every database, and syncing it is refused until the folder is back. Nothing else is affected, including starting the app.
- **Unregistering a folder that still feeds a database is refused.** The message names the databases and tells the user to disconnect it and use Sync all there first. This guarantees no database is left holding chunks from a source the app no longer knows.
- **Browse… when the folder dialog helper is not running:** a message says to start the app with its launch command or to type the path instead.
- **Browse… requests from any other web page are refused.** Only RAG Studio's own page may open the dialog.

## Related ideas

- [[Source]], [[Sync]], [[Host drives mount]]
