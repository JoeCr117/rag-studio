# Hugging Face

The main public website for sharing machine-learning models, from which RAG Studio downloads every model file and tokenizer.

- **Repositories:** each model lives in a repository named owner/name, such as Qwen/Qwen3-Embedding-0.6B-GGUF. The Models tab links to each.
- **No login needed:** the catalog lists only models that download without an account.
- **When:** on first use, or with Download on the Models tab.
- **Where they go:** the models [[Docker volume]].
- **How a download is written:** into a temporary `.incomplete` file, renamed to the model's name only when complete, so a half-downloaded model is never loaded by mistake.
- **No resume:** each attempt uses its own temporary file. This avoids two downloads corrupting one shared file, but an interrupted download starts over. RAG Studio deletes leftover partial files when it starts.
