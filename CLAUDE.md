# RAG Studio

Docker app for building vector databases from local folders, then searching and asking them. Commands and layout:
`README.md`.

## Stack

- Windows host; scripts are PowerShell. Python from `uv` only.
- Model lists and VRAM estimates are sized for a 12 GB NVIDIA GPU.
- Backend: Django + Django Ninja, Loguru, pytest, Ruff (`ruff.toml`, `backend/`). Frontend: Next.js, Vitest, oxlint (`web/`;
  ESLint's TypeScript support stops below TypeScript 7).
- Everything runs in Docker. Start with `start.ps1`; stop with the UI's Shut down button.
- Docker project name is fixed (`rag-studio`); volumes keep data wherever this folder lives.
- Before rebuilding, restarting or shutting down, check `GET /api/state` for queued or running jobs and ask first: a
  restart kills the running job, and model downloads start over (`backend/studio/model_downloads.py`).

## Architecture rules

- Never add per-source Docker mounts: the worker reads sources through one fixed read-only mount of every drive
  (`/host`), so a missing folder cannot block startup.
- Browse… uses Windows' own folder dialog from `folder-picker/folder_picker.py`, which runs on Windows outside Docker
  (started by `start.ps1`). Keep it standard-library only and reachable only from RAG Studio's page.
- Only the `control` service holds the Docker socket; app containers request fixed, validated actions from it.
- Engines implement `VectorEngine` (`backend/studio/databases/engines/base.py`): pgvector and Qdrant. Hybrid search
  fuses with RRF k=60 in both so scores compare.
- The GPU is optional. GPU-only compose settings belong in `compose.gpu.yaml`, which `start.ps1` adds when `nvidia-smi`
  works. Offer runtimes only through `backend/studio/runtimes.py`.
- Every GPU start (embedder, generator, reranker) goes through the VRAM check (`backend/studio/inference/servers.py`);
  a shortfall returns 409 and the UI offers Start anyway.
- Jobs run one at a time in the worker; finish jobs with an `update()` query, not `save()`.
- Call llama.cpp servers only through a `ModelServerClient` (`backend/studio/inference/model_server.py`), inside `with`:
  it closes connections and turns failures into `ModelServerError` (502 with the server's own message).
- Ask fits passages to the generator's window before generating (`backend/studio/search/context_budget.py`); never
  send passages unbudgeted.
- Requests that change state are refused unless they come from the UI's origin (`backend/studio/origin_guard.py`).

## Learning popups

- Explain UI concepts with `<Explained note="…">` (`web/components/Explained.tsx`), not `title=`. The note lives in
  `RAGStudioVault/`; write or change it following `RAGStudioVault/Vault Metadata.md`. Its first paragraph is the popup.

## Documenting features

Every feature change updates, in the same task:
- the `RAGStudioVault/RagStudio/` notes (behaviour only, no implementation; see `Vault Metadata.md`), which hold all
  behaviour; the README links to them instead of repeating it;
- `README.md` only when requirements, commands, the demonstrated stages or the code map change;
- the concept notes it touches;
- a learning popup for any new concept it puts on screen.

## Hardware rules

- Peak VRAM near the card's capacity spills to system RAM and speed collapses. Other apps may hold VRAM too; check the
  header's VRAM meter before benchmarking.
- Stop RAG Studio's generator and reranker before benchmarking anything else on the GPU: they hold VRAM while running.

## Verification

- Exercise every new UI control in the browser before reporting.
- Before reporting, pass `uvx ruff check .`, `uvx ruff format --check .`, and `npm run lint` / `npm run typecheck` in `web/`.
- After moving this folder, run `uv sync --reinstall` in `backend/`: `.exe` launchers in `.venv` record the old path.
