export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type AssignmentStatus = "synced" | "changed" | "never_synced" | "missing" | "disconnected";

export interface SourceAssignment {
  database_id: number;
  database_name: string;
  status: AssignmentStatus;
}

export interface Source {
  id: number;
  name: string;
  host_path: string;
  include_patterns: string;
  exclude_patterns: string;
  found: boolean;
  file_count: number | null;
  scanned_at: string | null;
  scan_error: string;
  assignments: SourceAssignment[];
}

export interface DatabaseAssignment {
  source_id: number;
  source_name: string;
  connected: boolean;
  status: AssignmentStatus;
  synced_at: string | null;
}

export interface DatabaseSettings {
  name: string;
  engine: string;
  embedding_model: string;
  embedder_runtime: string;
  chunk_min_tokens: number;
  chunk_max_tokens: number;
  chunk_overlap_tokens: number;
  search_mode: string;
}

export interface Database extends DatabaseSettings {
  id: number;
  embedder: string;
  running: boolean;
  ready: boolean;
  needs_rebuild: boolean;
  busy: boolean;
  counts: { documents: number; chunks: number } | null;
  warnings: string[];
  assignments: DatabaseAssignment[];
}

/** A running job's progress; `total` is null while the amount of work is unknown. */
export interface JobProgress {
  done: number;
  total: number | null;
  unit: "files" | "bytes";
  detail: string;
}

export interface Job {
  id: number;
  kind: string;
  status: "queued" | "running" | "done" | "failed";
  title: string;
  message: string;
  database_id: number | null;
  source_id: number | null;
  model_key: string;
  progress: JobProgress | null;
  created_at: string;
  finished_at: string | null;
}

export type DownloadStatus = "downloaded" | "downloading" | "missing";

export interface EmbeddingModelOption {
  key: string;
  label: string;
  repo: string;
  file: string;
  dimensions: number;
  pooling: string;
  query_prefix: string;
  document_prefix: string;
  size_gb: number;
  notes: string;
  download_status: DownloadStatus;
}

export type SearchMode = "hybrid" | "vector";

export interface SearchHit {
  document_id: number;
  source_id: number;
  source_name: string;
  path: string;
  chunk_index: number;
  content: string;
  score: number;
  similarity: number;
  semantic_rank: number | null;
  keyword_rank: number | null;
  rerank_score: number | null;
}

export interface SearchResponse {
  mode: SearchMode;
  embed_ms: number;
  search_ms: number;
  rerank_ms: number | null;
  rerank_pool: number | null;
  hits: SearchHit[];
}

export interface Completion {
  text: string;
  prompt_tokens: number;
  completion_tokens: number;
  prompt_ms: number;
  generation_ms: number;
  tokens_per_second: number;
  /** The model's thinking, kept apart from the answer; empty when thinking was off or unsupported. */
  reasoning: string;
  /** `"length`" when the output allowance ran out and the answer is cut off. */
  finish_reason: string;
}

/** How the generator's context window was shared between the passages and the answer. */
export interface ContextBudget {
  window: number;
  output_allowance: number;
  passages_found: number;
  passages_used: number;
  passages_left_out: number;
}

export interface AskResponse {
  answer: string;
  /** Whether thinking was asked for. */
  think: boolean;
  completion: Completion;
  context: ContextBudget;
  /** Only the passages the generator received, numbered as in its context. */
  search: SearchResponse;
}

export interface SearchRequest {
  query: string;
  limit: number;
  mode: string;
  rerank_pool: number | null;
}

export interface GeneratorModelOption {
  key: string;
  label: string;
  repo: string;
  file: string;
  size_gb: number;
  vram_gb: number;
  kv_gb_per_8k: number;
  cpu_moe_layers: number;
  notes: string;
  download_status: DownloadStatus;
  vram_estimate_gb: number;
}

export interface RerankerModelOption {
  key: string;
  label: string;
  repo: string;
  file: string;
  size_gb: number;
  vram_gb: number;
  notes: string;
  download_status: DownloadStatus;
}

/** A file or folder in the shared models volume, as the containers and Windows Explorer see it. */
export interface VolumeLocation {
  container_path: string;
  windows_path: string;
  source_url: string;
  present: boolean;
}

/** A model that ships inside a service's image: nothing is downloaded or stored in the models volume. */
export interface BuiltInModel {
  key: string;
  label: string;
  /** Vault note explaining it. */
  note: string;
  used_for: string;
  service: string;
  image: string;
  image_paths: string[];
  notes: string;
}

export interface ModelLocations {
  volume: { container_path: string; windows_path: string };
  files: Record<string, VolumeLocation>;
  tokenizers: Record<string, VolumeLocation>;
  built_in: BuiltInModel[];
}

export type ServerRole = "generator" | "reranker";

export interface ServerState {
  model_key: string | null;
  runtime: string | null;
  context: number | null;
  running: boolean;
  busy: boolean;
  vram_gb: number;
}

export interface Vram {
  used_mib: number;
  total_mib: number;
}

export interface StoredDocument {
  id: number;
  source_id: number;
  source_name: string;
  path: string;
  chunks: number;
  ingested_at: string;
}

export interface StoredChunk {
  index: number;
  content: string;
  embedding_text: string;
  dimensions: number;
  vector_preview: number[];
  norm: number;
}

export interface Options {
  engines: string[];
  embedding_models: EmbeddingModelOption[];
  /** Only `"cpu`" when start.ps1 found no NVIDIA GPU. */
  runtimes: string[];
  search_modes: string[];
  chunk_min_tokens: number[];
  chunk_max_tokens: number[];
  chunk_overlap_tokens: number[];
  defaults: Omit<DatabaseSettings, "name">;
  generator_models: GeneratorModelOption[];
  reranker_models: RerankerModelOption[];
  generator_contexts: number[];
}

export interface StudioState {
  sources: Source[];
  databases: Database[];
  jobs: Job[];
  model_locations: ModelLocations;
  servers: Record<ServerRole, ServerState>;
  gpu_available: boolean;
  vram: Vram | null;
  options: Options;
}

/** The API's status for "this GPU start probably does not fit"; resending with force starts it anyway. */
export const VRAM_WARNING = 409;

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function request<T = unknown>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_URL}/api${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof payload.detail === "string" ? payload.detail : `${method} ${path} failed (${response.status})`;
    throw new ApiError(message, response.status);
  }
  return payload as T;
}
