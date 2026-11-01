"use client";

import { useEffect, useState } from "react";

import { DatabasePicker } from "@/components/DatabasePicker";
import { Explained } from "@/components/Explained";
import { request, type Database, type StoredChunk, type StoredDocument } from "@/lib/api";
import { vectorPreviewText } from "@/lib/explore";

interface Props {
  databases: Database[];
  selected: Database;
  onSelect: (id: number) => void;
}

export function BrowsePanel({ databases, selected, onSelect }: Props) {
  const [sourceId, setSourceId] = useState("");
  const [pathFilter, setPathFilter] = useState("");
  const [documents, setDocuments] = useState<StoredDocument[]>([]);
  const [opened, setOpened] = useState<StoredDocument | null>(null);
  const [loaded, setLoaded] = useState<{ documentId: number; chunks: StoredChunk[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const documentCount = selected.counts?.documents ?? 0;
  const chunks = opened && loaded?.documentId === opened.id ? loaded.chunks : [];

  useEffect(() => {
    const query = new URLSearchParams({ path: pathFilter });
    if (sourceId) query.set("source_id", sourceId);
    request<{ documents: StoredDocument[] }>("GET", `/databases/${selected.id}/documents?${query}`)
      .then((payload) => { setDocuments(payload.documents); setError(null); })
      .catch((failure) => setError(failure instanceof Error ? failure.message : String(failure)));
    // oxlint-disable-next-line react/exhaustive-effect-dependencies -- refetch when a sync changes the document count
  }, [selected.id, sourceId, pathFilter, documentCount]);

  useEffect(() => {
    if (!opened) return;
    request<{ chunks: StoredChunk[] }>("GET", `/databases/${selected.id}/documents/${opened.id}/chunks`)
      .then((payload) => setLoaded({ documentId: opened.id, chunks: payload.chunks }))
      .catch((failure) => setError(failure instanceof Error ? failure.message : String(failure)));
  }, [selected.id, opened]);

  return (
    <section className="panel explore">
      <div className="card form">
        <div className="grid-2">
          <DatabasePicker databases={databases} selected={selected} onSelect={onSelect} />
          <label>
            Source
            <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
              <option value="">All sources</option>
              {selected.assignments.map((assignment) => (
                <option key={assignment.source_id} value={assignment.source_id}>{assignment.source_name}</option>
              ))}
            </select>
          </label>
          <label>
            Path contains
            <input value={pathFilter} onChange={(e) => setPathFilter(e.target.value)} placeholder="e.g. notes/" />
          </label>
        </div>
        {error && <p className="error-text">{error}</p>}
      </div>
      <div className="browse">
        <div>
          <p className="meta"><Explained note="Document">{documents.length} documents</Explained></p>
          <ul className="list documents">
            {documents.map((document) => (
              <li key={document.id}>
                <button className={opened?.id === document.id ? "document selected" : "document"} onClick={() => setOpened(document)}>
                  <code>{document.path}</code>
                  <span className="hint">{document.source_name} · {document.chunks} chunk{document.chunks === 1 ? "" : "s"}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div className="min-0">
          {opened ? (
            <>
              <h2><code>{opened.path}</code></h2>
              <p className="meta">{chunks.length} chunks · ingested {new Date(opened.ingested_at).toLocaleString()}</p>
              {chunks.map((chunk) => <ChunkCard key={chunk.index} chunk={chunk} />)}
            </>
          ) : (
            <p className="hint">Pick a document to see how it was split and embedded.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function ChunkCard({ chunk }: { chunk: StoredChunk }) {
  return (
    <div className="card">
      <div className="row">
        <strong><Explained note="Chunk">Chunk {chunk.index}</Explained></strong>
        <span className="pill">{chunk.content.length} chars</span>
        <Explained note="Dimensions" asChild><span className="pill">{chunk.dimensions} dims</span></Explained>
        <Explained note="Vector norm" asChild><span className="pill">norm {chunk.norm.toFixed(3)}</span></Explained>
      </div>
      <pre className="chunk-text">{chunk.content}</pre>
      <details>
        <summary><Explained note="File header">Embedded text and vector</Explained></summary>
        <p className="hint">The chunk with its source and path header, as embedded (the model&apos;s document prefix, if any, is added on top).</p>
        <pre className="chunk-text">{chunk.embedding_text}</pre>
        <code className="path">{vectorPreviewText(chunk.vector_preview, chunk.dimensions)}</code>
      </details>
    </div>
  );
}
