# File patterns

Rules, in the same syntax as a .gitignore file, that pick which files in a source are read.

- **Include:** one pattern per line, such as `*.md`. Empty means Markdown, plain text and common code files.
- **Exclude:** files or folders to skip, such as `drafts/`. Folders like `.git`, `node_modules` and `.venv` are always skipped, as are files over 2 MB (megabytes) and anything a `.gitignore` inside the source ignores.
- **Why it matters:** every file read becomes [[Chunk|chunks]] and vectors. Leaving out generated or irrelevant files keeps search results on topic and syncs fast.
- **Changing them:** the next [[Sync]] adds newly included files and removes newly excluded ones.
