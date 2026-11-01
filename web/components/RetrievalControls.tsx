import type { Database, SearchRequest } from "@/lib/api";

import { Explained } from "./Explained";

const RESULT_COUNTS = [3, 5, 8, 10, 20, 50];
const RERANK_POOLS = [20, 30, 50, 100];

export interface RetrievalSettings {
  limit: number;
  mode: string;
  rerank: boolean;
  pool: number;
}

export const DEFAULT_RETRIEVAL: RetrievalSettings = { limit: 8, mode: "", rerank: false, pool: 30 };

export function searchRequest(query: string, settings: RetrievalSettings): SearchRequest {
  return { query, limit: settings.limit, mode: settings.mode, rerank_pool: settings.rerank ? settings.pool : null };
}

interface Props {
  database: Database;
  settings: RetrievalSettings;
  onChange: (settings: RetrievalSettings) => void;
  rerankBlocker: string | null;
}

/** Mode, result count and reranking, shared by the Search and Ask tabs. */
export function RetrievalControls({ database, settings, onChange, rerankBlocker }: Props) {
  const set = <K extends keyof RetrievalSettings>(field: K, value: RetrievalSettings[K]) => onChange({ ...settings, [field]: value });
  return (
    <>
      <label>
        <Explained note="Hybrid search">Mode</Explained>
        <select value={settings.mode} onChange={(e) => set("mode", e.target.value)}>
          <option value="">Database default ({database.search_mode})</option>
          <option value="hybrid">Hybrid (vector + keyword, RRF)</option>
          <option value="vector">Vector only</option>
        </select>
      </label>
      <label>
        <Explained note="Top-k">Results</Explained>
        <select value={settings.limit} onChange={(e) => set("limit", Number(e.target.value))}>
          {RESULT_COUNTS.map((count) => <option key={count} value={count}>{count}</option>)}
        </select>
      </label>
      <label>
        <Explained note="Reranking" detail={rerankBlocker ?? undefined}>Rerank</Explained>
        <span className="row">
          <input
            type="checkbox"
            checked={settings.rerank && !rerankBlocker}
            disabled={!!rerankBlocker}
            onChange={(e) => set("rerank", e.target.checked)}
            aria-label="Rerank"
          />
          <select value={settings.pool} disabled={!settings.rerank || !!rerankBlocker} onChange={(e) => set("pool", Number(e.target.value))} aria-label="Rerank candidates">
            {RERANK_POOLS.map((pool) => <option key={pool} value={pool}>from {pool} candidates</option>)}
          </select>
        </span>
      </label>
    </>
  );
}
