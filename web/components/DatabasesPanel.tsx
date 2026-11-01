"use client";

import { useState } from "react";

import { request, type Database, type DatabaseSettings, type StudioState } from "@/lib/api";
import { needsSync, unassignedSources } from "@/lib/status";
import type { Act, StartGpu } from "@/lib/useStudioState";

import { DatabaseForm } from "./DatabaseForm";
import { Explained } from "./Explained";
import { JobActivity } from "./JobActivity";
import { StatusPill } from "./StatusPill";

export function DatabasesPanel({ state, act, startGpu }: { state: StudioState; act: Act; startGpu: StartGpu }) {
  const [creating, setCreating] = useState(false);

  return (
    <section className="panel">
      <div className="row">
        <h2><Explained note="Vector Databases">Vector databases</Explained></h2>
        <span className="spacer" />
        {!creating && <button className="button button-primary" onClick={() => setCreating(true)}>New database</button>}
      </div>
      {creating && (
        <DatabaseForm
          options={state.options}
          submitLabel="Create database"
          onSubmit={(settings) => act(() => request("POST", "/databases", settings))}
          onCancel={() => setCreating(false)}
        />
      )}
      {state.databases.length === 0 && !creating && <p className="hint">No databases yet.</p>}
      <ul className="list">
        {state.databases.map((database) => (
          <DatabaseCard key={database.id} database={database} state={state} act={act} startGpu={startGpu} />
        ))}
      </ul>
    </section>
  );
}

function DatabaseCard({ database, state, act, startGpu }: { database: Database; state: StudioState; act: Act; startGpu: StartGpu }) {
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const available = unassignedSources(state.sources, database);
  const base = `/databases/${database.id}`;
  const model = state.options.embedding_models.find((option) => option.key === database.embedding_model);

  if (editing) {
    return (
      <li>
        <DatabaseForm
          options={state.options}
          initial={database}
          rebuildWarning={database.ready}
          submitLabel="Save settings"
          onSubmit={(settings: DatabaseSettings) => act(() => request("PUT", base, settings))}
          onCancel={() => setEditing(false)}
        />
      </li>
    );
  }

  return (
    <li className="card">
      <div className="row">
        <strong>{database.name}</strong>
        <Explained
          note="Embedder"
          detail={database.running ? "Its embedder is running, so it can sync and search." : "Its embedder is stopped: start the database to sync or search."}
          asChild
        >
          <span className={database.running ? "pill pill-good" : "pill"}>{database.running ? "Running" : "Stopped"}</span>
        </Explained>
        {!database.ready && <span className="pill pill-warn">Creating…</span>}
        {database.busy && <span className="pill pill-busy">Working…</span>}
        <span className="spacer" />
        <button
          className="button"
          disabled={!database.ready}
          onClick={() =>
            database.running
              ? act(() => request("POST", `${base}/stop`))
              : startGpu((force) => request("POST", `${base}/start${force ? "?force=true" : ""}`))
          }
        >
          {database.running ? "Stop" : "Start"}
        </button>
        <button
          className={database.warnings.length ? "button button-accent" : "button"}
          disabled={!database.running}
          title={database.running ? "Sync every connected source, remove disconnected ones, rebuild if needed" : "Start the database first"}
          onClick={() => act(() => request("POST", `${base}/sync-all`))}
        >
          Sync all
        </button>
      </div>
      <p className="meta">
        <Explained note="Vector engine">{database.engine}</Explained>
        {" · "}<Explained note="Embedding model">{model?.label ?? database.embedding_model}</Explained>
        {" · "}<Explained note="CPU and GPU inference">{database.embedder_runtime.toUpperCase()}</Explained>
        {" · "}<Explained note="Chunk size">chunks {database.chunk_min_tokens}–{database.chunk_max_tokens} tokens</Explained>
        {", "}<Explained note="Chunk overlap">overlap {database.chunk_overlap_tokens}</Explained>
        {" · "}<Explained note="Hybrid search">{database.search_mode}</Explained>
        {database.counts && (
          <>
            {" · "}<Explained note="Document">{database.counts.documents} documents</Explained>
            {", "}<Explained note="Chunk">{database.counts.chunks} chunks</Explained>
          </>
        )}
      </p>
      {database.warnings.map((warning) => (
        <p key={warning} className="warn-text">{warning}</p>
      ))}
      <JobActivity jobs={state.jobs} matches={(job) => job.database_id === database.id} />
      <table className="assignments">
        <tbody>
          {database.assignments.length === 0 && (
            <tr><td className="hint">No sources assigned.</td></tr>
          )}
          {database.assignments.map((assignment) => (
            <tr key={assignment.source_id} className={assignment.connected ? "" : "disconnected"}>
              <td>{assignment.source_name}</td>
              <td><StatusPill status={assignment.status} /></td>
              <td className="actions">
                {assignment.connected ? (
                  <>
                    <button
                      className={needsSync(assignment.status) ? "button button-accent" : "button"}
                      disabled={!database.running || assignment.status === "missing"}
                      title={database.running ? "" : "Start the database first"}
                      onClick={() => act(() => request("POST", `${base}/sources/${assignment.source_id}/sync`))}
                    >
                      {needsSync(assignment.status) ? "Resync" : "Sync"}
                    </button>
                    <button className="link" onClick={() => act(() => request("POST", `${base}/sources/${assignment.source_id}/disconnect`))}>
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button className="link" onClick={() => act(() => request("POST", `${base}/sources/${assignment.source_id}/connect`))}>
                    Reconnect
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="row">
        {available.length > 0 && (
          <select
            aria-label={`Connect a source to ${database.name}`}
            value=""
            onChange={(e) => act(() => request("POST", `${base}/sources/${e.target.value}/connect`))}
          >
            <option value="">Connect source…</option>
            {available.map((source) => (
              <option key={source.id} value={source.id}>{source.name}</option>
            ))}
          </select>
        )}
        <button className="link" onClick={() => setEditing(true)}>Edit settings</button>
        <span className="spacer" />
        {confirmDelete ? (
          <>
            <button
              className="button button-danger"
              onClick={() => act(() => request("DELETE", base)).finally(() => setConfirmDelete(false))}
            >
              Confirm delete
            </button>
            <button className="link" onClick={() => setConfirmDelete(false)}>Cancel</button>
          </>
        ) : (
          <button className="link" onClick={() => setConfirmDelete(true)}>Delete</button>
        )}
      </div>
    </li>
  );
}
