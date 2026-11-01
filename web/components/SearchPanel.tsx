"use client";

import { useState, type FormEvent } from "react";

import { DatabasePicker } from "@/components/DatabasePicker";
import { HitList } from "@/components/HitList";
import { DEFAULT_RETRIEVAL, RetrievalControls, searchRequest } from "@/components/RetrievalControls";
import { request, type Database, type SearchResponse, type StudioState } from "@/lib/api";
import { searchBlocker } from "@/lib/explore";
import { rerankBlocker } from "@/lib/inference";

interface Props {
  databases: Database[];
  selected: Database;
  onSelect: (id: number) => void;
  servers: StudioState["servers"];
}

export function SearchPanel({ databases, selected, onSelect, servers }: Props) {
  const [query, setQuery] = useState("");
  const [retrieval, setRetrieval] = useState(DEFAULT_RETRIEVAL);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const blocker = searchBlocker(selected);
  const rerankUnavailable = rerankBlocker(servers);

  async function search(event: FormEvent) {
    event.preventDefault();
    setSearching(true);
    try {
      const body = searchRequest(query, { ...retrieval, rerank: retrieval.rerank && !rerankUnavailable });
      setResult(await request<SearchResponse>("POST", `/databases/${selected.id}/search`, body));
      setError(null);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setSearching(false);
    }
  }

  return (
    <section className="panel explore">
      <form className="card form" onSubmit={search}>
        <div className="grid-2">
          <DatabasePicker databases={databases} selected={selected} onSelect={onSelect} />
          <RetrievalControls database={selected} settings={retrieval} onChange={setRetrieval} rerankBlocker={rerankUnavailable} />
        </div>
        <div className="row">
          <input className="grow" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ask the database something…" aria-label="Query" />
          <button className="button button-primary" disabled={!!blocker || searching || !query.trim()}>
            {searching ? "Searching…" : "Search"}
          </button>
        </div>
        {blocker && <p className="warn-text">{blocker}</p>}
        {error && <p className="error-text">{error}</p>}
      </form>
      {result && <HitList result={result} />}
    </section>
  );
}
