import type { Database, EmbeddingModelOption, SearchHit } from "./api";

/** Keeps the chosen database while it exists, otherwise prefers one that can answer a search right now. */
export function pickDatabase(databases: Database[], chosenId: number | null): Database | null {
  return (
    databases.find((database) => database.id === chosenId) ??
    databases.find((database) => database.running && !database.needs_rebuild) ??
    databases[0] ??
    null
  );
}

/** Why a database cannot run a search, or null when it can. */
export function searchBlocker(database: Database): string | null {
  if (!database.running) return "Start this database first: its embedder turns the query into a vector.";
  if (database.needs_rebuild) return "Settings changed since its vectors were made: run Sync all to rebuild it.";
  if (!database.counts?.chunks) return "Nothing ingested yet: connect a source and sync it.";
  return null;
}

export function rankSummary(hit: SearchHit): string {
  const rank = (value: number | null) => (value === null ? "—" : `#${value}`);
  return `vector ${rank(hit.semantic_rank)} · keyword ${rank(hit.keyword_rank)}`;
}

export function modelOptionLabel(model: EmbeddingModelOption): string {
  if (model.download_status === "downloaded") return model.label;
  if (model.download_status === "downloading") return `${model.label} — downloading`;
  return `${model.label} — ${model.size_gb} GB download on Start`;
}

export function vectorPreviewText(values: number[], dimensions: number): string {
  const shown = values.map((value) => value.toFixed(4)).join(", ");
  return dimensions > values.length ? `[${shown}, … ${dimensions - values.length} more]` : `[${shown}]`;
}
