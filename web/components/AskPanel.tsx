"use client";

import { useState, type FormEvent } from "react";

import { DatabasePicker } from "@/components/DatabasePicker";
import { Explained } from "@/components/Explained";
import { HitList } from "@/components/HitList";
import { MarkdownAnswer } from "@/components/MarkdownAnswer";
import { DEFAULT_RETRIEVAL, RetrievalControls, searchRequest } from "@/components/RetrievalControls";
import { ServersPanel } from "@/components/ServersPanel";
import { request, type AskResponse, type Database, type StudioState } from "@/lib/api";
import { askBlocker, citedPassages, cutOffNotice, leftOutNotice, rerankBlocker, thinkingNotice } from "@/lib/inference";
import type { Act, StartGpu } from "@/lib/useStudioState";

interface Props {
  state: StudioState;
  act: Act;
  startGpu: StartGpu;
  selected: Database;
  onSelect: (id: number) => void;
}

export function AskPanel({ state, act, startGpu, selected, onSelect }: Props) {
  const [question, setQuestion] = useState("");
  const [retrieval, setRetrieval] = useState({ ...DEFAULT_RETRIEVAL, limit: 5 });
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const [think, setThink] = useState(false);
  const blocker = askBlocker(selected, state.servers);
  const rerankUnavailable = rerankBlocker(state.servers);

  async function ask(event: FormEvent) {
    event.preventDefault();
    setAsking(true);
    try {
      const body = { ...searchRequest(question, { ...retrieval, rerank: retrieval.rerank && !rerankUnavailable }), think };
      setResult(await request<AskResponse>("POST", `/databases/${selected.id}/ask`, body));
      setError(null);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setAsking(false);
    }
  }

  return (
    <section className="panel explore">
      <ServersPanel state={state} act={act} startGpu={startGpu} />
      <form className="card form" onSubmit={ask}>
        <div className="grid-2">
          <DatabasePicker databases={state.databases} selected={selected} onSelect={onSelect} />
          <RetrievalControls database={selected} settings={retrieval} onChange={setRetrieval} rerankBlocker={rerankUnavailable} />
        </div>
        <textarea
          className="question"
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about the documents in this database…"
          aria-label="Question"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              e.currentTarget.form?.requestSubmit();
            }
          }}
        />
        <div className="row">
          <button className="button button-primary" disabled={!!blocker || asking || !question.trim()}>
            {asking ? (think ? "Retrieving, thinking and generating…" : "Retrieving and generating…") : "Ask"}
          </button>
          <label className="row toggle">
            <input type="checkbox" checked={think} onChange={(e) => setThink(e.target.checked)} />
            <Explained note="Thinking mode" detail="Slower: the model writes its reasoning first, often hundreds of tokens.">
              Think first
            </Explained>
          </label>
          <span className="hint">Enter to ask, Shift+Enter for a new line.</span>
        </div>
        {blocker && <p className="warn-text">{blocker}</p>}
        {error && <p className="error-text">{error}</p>}
      </form>
      {result && <AnswerView result={result} />}
    </section>
  );
}

function AnswerView({ result }: { result: AskResponse }) {
  const { completion } = result;
  const notices = [thinkingNotice(result), cutOffNotice(result)].filter(Boolean);
  const leftOut = leftOutNotice(result.context);
  return (
    <>
      <div className="card answer">
        <h2><Explained note="Retrieval-Augmented Generation">Answer</Explained></h2>
        {completion.reasoning && (
          <details className="thinking">
            <summary>
              <Explained note="Thinking mode">Thinking</Explained>{" "}
              <span className="hint">({completion.reasoning.split(/\s+/).filter(Boolean).length} words, not part of the answer)</span>
            </summary>
            <pre className="chunk-text">{completion.reasoning}</pre>
          </details>
        )}
        {notices.map((notice) => <p key={notice} className="warn-text">{notice}</p>)}
        <MarkdownAnswer text={result.answer} />
        <div className="chips">
          <Explained note="Prefill" asChild>
            <span className="pill">prefill {completion.prompt_tokens} tokens in {completion.prompt_ms} ms</span>
          </Explained>
          <Explained note="Decoding" asChild>
            <span className="pill">
              generated {completion.completion_tokens} tokens{completion.reasoning ? " (thinking included)" : ""} in {completion.generation_ms} ms
            </span>
          </Explained>
          <Explained note="Tokens per second" asChild>
            <span className="pill pill-good">{completion.tokens_per_second} tok/s</span>
          </Explained>
          <Explained note="Context budget" asChild>
            <span className={`pill ${leftOut ? "pill-busy" : ""}`}>
              {result.context.passages_used} of {result.context.passages_found} passages fit · {result.context.window.toLocaleString("en-US")}-token window
            </span>
          </Explained>
        </div>
      </div>
      <h2><Explained note="Passages">Passages given to the generator</Explained></h2>
      {leftOut && <p className="warn-text">{leftOut}</p>}
      <HitList result={result.search} cited={citedPassages(result.answer)} numbering="passage" />
    </>
  );
}
