"use client";

import { useState, type FormEvent } from "react";

import { request, type Source, type StudioState } from "@/lib/api";
import { pickFolder } from "@/lib/folderPicker";
import { needsSync, syncTargets, unassignedDatabases } from "@/lib/status";
import type { Act } from "@/lib/useStudioState";

import { Explained } from "./Explained";
import { JobActivity } from "./JobActivity";
import { StatusPill } from "./StatusPill";

export function SourcesPanel({ state, act }: { state: StudioState; act: Act }) {
  return (
    <section className="panel">
      <h2><Explained note="Source">Sources</Explained></h2>
      <p className="hint">
        Folders on this machine, <Explained note="Host drives mount">read-only</Explained>; the app never changes them.
      </p>
      <RegisterSourceForm act={act} />
      {state.sources.length === 0 && <p className="hint">No sources registered yet.</p>}
      <ul className="list">
        {state.sources.map((source) => (
          <SourceRow key={source.id} source={source} state={state} act={act} />
        ))}
      </ul>
    </section>
  );
}

function RegisterSourceForm({ act }: { act: Act }) {
  const [hostPath, setHostPath] = useState("");
  const [name, setName] = useState("");
  const [include, setInclude] = useState("");
  const [exclude, setExclude] = useState("");
  const [checking, setChecking] = useState(false);
  const [picking, setPicking] = useState(false);
  const [pickError, setPickError] = useState<string | null>(null);

  async function browse() {
    setPicking(true);
    setPickError(null);
    try {
      const chosen = await pickFolder(hostPath.trim());
      if (chosen) setHostPath(chosen);
    } catch (failure) {
      setPickError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setPicking(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setChecking(true);
    const body = { host_path: hostPath, name, include_patterns: include, exclude_patterns: exclude };
    const ok = await act(() => request("POST", "/sources", body));
    setChecking(false);
    if (ok) {
      setHostPath("");
      setName("");
      setInclude("");
      setExclude("");
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <div className="field">
        <label htmlFor="source-path">Path on this machine</label>
        <div className="row">
          <input
            id="source-path"
            className="grow"
            value={hostPath}
            onChange={(e) => setHostPath(e.target.value)}
            placeholder="W:\Notes\Project"
            required
          />
          <button type="button" className="button" disabled={picking} onClick={browse}>
            {picking ? "Choose in the Windows dialog…" : "Browse…"}
          </button>
        </div>
        {pickError && <p className="error-text">{pickError}</p>}
      </div>
      <label>
        Name <span className="hint">(optional, defaults to the folder name)</span>
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      <details>
        <summary><Explained note="File patterns">File patterns</Explained></summary>
        <PatternFields include={include} exclude={exclude} onInclude={setInclude} onExclude={setExclude} />
      </details>
      <button className="button button-primary" disabled={checking || !hostPath.trim()}>
        {checking ? "Checking path…" : "Register source"}
      </button>
    </form>
  );
}

function PatternFields(props: { include: string; exclude: string; onInclude: (v: string) => void; onExclude: (v: string) => void }) {
  return (
    <div className="pattern-fields">
      <label>
        Include <span className="hint">(one per line; empty = Markdown, text and code)</span>
        <textarea rows={3} value={props.include} onChange={(e) => props.onInclude(e.target.value)} placeholder="*.md" />
      </label>
      <label>
        Exclude <span className="hint">(.gitignore syntax; .git, node_modules, .venv… always skipped)</span>
        <textarea rows={3} value={props.exclude} onChange={(e) => props.onExclude(e.target.value)} placeholder="drafts/" />
      </label>
    </div>
  );
}

function SourceRow({ source, state, act }: { source: Source; state: StudioState; act: Act }) {
  const [editing, setEditing] = useState(false);
  const [include, setInclude] = useState(source.include_patterns);
  const [exclude, setExclude] = useState(source.exclude_patterns);
  const [confirmRemove, setConfirmRemove] = useState(false);
  const available = unassignedDatabases(state.databases, source);
  const targets = syncTargets(state.databases, source);
  const outOfDate = source.assignments.some((assignment) => needsSync(assignment.status));

  function syncEverywhere() {
    return act(() => Promise.all(targets.map((database) => request("POST", `/databases/${database.id}/sources/${source.id}/sync`))));
  }

  return (
    <li className="card">
      <div className="row">
        <strong>{source.name}</strong>
        {source.found ? (
          <span className="pill pill-good">{source.file_count ?? 0} files</span>
        ) : (
          <Explained note="Source" detail="Moved, deleted or its drive disconnected. It is picked up again once it is back." asChild>
            <span className="pill pill-warn">Folder missing</span>
          </Explained>
        )}
        <span className="spacer" />
        <button
          className={outOfDate ? "button button-accent" : "button"}
          disabled={targets.length === 0}
          title={targets.length ? `Sync into ${targets.map((d) => d.name).join(", ")}` : "Connect it to a running database first"}
          onClick={syncEverywhere}
        >
          {outOfDate ? "Resync" : "Sync"}
        </button>
      </div>
      <code className="path">{source.host_path}</code>
      {source.scan_error && <p className="error-text">{source.scan_error}</p>}
      <JobActivity jobs={state.jobs} matches={(job) => job.source_id === source.id} />
      <div className="chips">
        {source.assignments.length === 0 && <span className="hint">Not assigned to any database.</span>}
        {source.assignments.map((assignment) => (
          <StatusPill key={assignment.database_id} status={assignment.status} prefix={assignment.database_name} />
        ))}
      </div>
      <div className="row">
        {available.length > 0 && (
          <select
            aria-label={`Assign ${source.name} to a database`}
            value=""
            onChange={(e) => act(() => request("POST", `/databases/${e.target.value}/sources/${source.id}/connect`))}
          >
            <option value="">Assign to database…</option>
            {available.map((database) => (
              <option key={database.id} value={database.id}>{database.name}</option>
            ))}
          </select>
        )}
        <button className="link" onClick={() => setEditing((open) => !open)}>{editing ? "Close patterns" : "Edit patterns"}</button>
        <span className="spacer" />
        {confirmRemove ? (
          <>
            <button
              className="button button-danger"
              onClick={() => act(() => request("DELETE", `/sources/${source.id}`)).finally(() => setConfirmRemove(false))}
            >
              Confirm unregister
            </button>
            <button className="link" onClick={() => setConfirmRemove(false)}>Cancel</button>
          </>
        ) : (
          <button className="link" onClick={() => setConfirmRemove(true)}>Unregister</button>
        )}
      </div>
      {editing && (
        <div className="form">
          <PatternFields include={include} exclude={exclude} onInclude={setInclude} onExclude={setExclude} />
          <button
            className="button"
            onClick={() => act(() => request("PUT", `/sources/${source.id}/patterns`, { include_patterns: include, exclude_patterns: exclude }))}
          >
            Save patterns
          </button>
        </div>
      )}
    </li>
  );
}
