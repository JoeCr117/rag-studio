import type { SearchResponse } from "@/lib/api";
import { rankSummary } from "@/lib/explore";

import { Explained } from "./Explained";

interface Props {
  result: SearchResponse;
  cited?: Set<number>;
  /** Ask numbers passages [1], [2]...; search lists ranks #1, #2... */
  numbering?: "rank" | "passage";
}

export function HitList({ result, cited, numbering = "rank" }: Props) {
  const reranked = result.rerank_ms !== null;
  const hybrid = result.mode === "hybrid";
  return (
    <>
      <p className="meta">
        {result.hits.length} hits · <Explained note={hybrid ? "Hybrid search" : "Vector search"}>{result.mode}</Explained>
        {" · "}<Explained note="Embeddings">embed {result.embed_ms} ms</Explained> · search {result.search_ms} ms
        {reranked && (
          <>
            {" · "}<Explained note="Candidate pool">rerank {result.rerank_ms} ms ({result.rerank_pool} candidates)</Explained>
          </>
        )}
      </p>
      <p className="hint">
        {reranked && "Order = reranker relevance (0–1), read from the query and chunk together. "}
        {hybrid
          ? "Score = Reciprocal Rank Fusion: 1/(60 + rank) summed over the vector and keyword lists (max ≈ 0.033). Similarity = cosine similarity of the query and chunk vectors."
          : "Score = cosine similarity: 1 means the vectors point the same way, 0 unrelated."}
      </p>
      {result.hits.length === 0 && <p className="hint">No chunks matched.</p>}
      <ol className="hits">
        {result.hits.map((hit, position) => {
          const number = position + 1;
          const isCited = cited?.has(number);
          return (
            <li key={`${hit.document_id}-${hit.chunk_index}`} className={isCited ? "card cited" : "card"}>
              <div className="row">
                {numbering === "passage" ? (
                  <Explained note="Passages" asChild><strong>[{number}]</strong></Explained>
                ) : (
                  <strong>#{number}</strong>
                )}
                {isCited && <Explained note="Citations" asChild><span className="pill pill-good">cited</span></Explained>}
                {hit.rerank_score !== null && (
                  <Explained note="Rerank score" asChild><span className="pill pill-busy">rerank {hit.rerank_score.toFixed(3)}</span></Explained>
                )}
                <Explained note={hybrid ? "Reciprocal Rank Fusion" : "Cosine similarity"} asChild>
                  <span className="pill">score {hit.score.toFixed(4)}</span>
                </Explained>
                <Explained note="Cosine similarity" asChild><span className="pill">similarity {hit.similarity.toFixed(3)}</span></Explained>
                {hybrid && <Explained note="Hybrid search" asChild><span className="hint">{rankSummary(hit)}</span></Explained>}
                <span className="spacer" />
                <span className="hint">{hit.source_name}</span>
              </div>
              <code className="path">{hit.path} · chunk {hit.chunk_index}</code>
              <pre className="chunk-text">{hit.content}</pre>
            </li>
          );
        })}
      </ol>
    </>
  );
}
