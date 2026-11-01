"use client";

import { useState } from "react";

import { request, type ServerState, type StudioState } from "@/lib/api";
import { generatorOptionLabel, initialRuntime, serverStatus } from "@/lib/inference";
import type { Act, StartGpu } from "@/lib/useStudioState";

import { Explained } from "./Explained";
import { JobActivity } from "./JobActivity";

const STATUS_CLASS = { running: "pill-good", busy: "pill-busy", stopped: "" } as const;
const GENERATOR_JOBS = ["start_generator", "stop_generator"];
const RERANKER_JOBS = ["start_reranker", "stop_reranker"];

interface Props {
  state: StudioState;
  act: Act;
  startGpu: StartGpu;
}

/** The shared generator and reranker containers, each on the CPU or, when the install has one, the GPU. */
export function ServersPanel({ state, act, startGpu }: Props) {
  return (
    <div className="grid-2 servers">
      <GeneratorCard state={state} act={act} startGpu={startGpu} />
      <RerankerCard state={state} act={act} startGpu={startGpu} />
    </div>
  );
}

function ServerHeading({ title, note, server }: { title: string; note: string; server: ServerState }) {
  const status = serverStatus(server);
  return (
    <div className="row">
      <strong><Explained note={note}>{title}</Explained></strong>
      <span className={`pill ${STATUS_CLASS[status]}`}>{status === "busy" ? "starting / stopping" : status}</span>
      {server.running && server.vram_gb > 0 && (
        <Explained note="VRAM" asChild><span className="hint">≈{server.vram_gb.toFixed(1)} GB VRAM</span></Explained>
      )}
    </div>
  );
}

interface RuntimeFieldProps {
  runtimes: string[];
  value: string;
  onChange: (runtime: string) => void;
  gpuLabel: string;
}

function RuntimeField({ runtimes, value, onChange, gpuLabel }: RuntimeFieldProps) {
  return (
    <label>
      <Explained note="CPU and GPU inference">Runs on</Explained>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {runtimes.map((option) => <option key={option} value={option}>{option === "gpu" ? gpuLabel : "CPU"}</option>)}
      </select>
    </label>
  );
}

function GeneratorCard({ state, act, startGpu }: Props) {
  const server = state.servers.generator;
  const models = state.options.generator_models;
  const [modelKey, setModelKey] = useState(server.model_key ?? models[0].key);
  const [context, setContext] = useState(server.context ?? 8192);
  const [runtime, setRuntime] = useState(initialRuntime(server.runtime, state.options.runtimes));
  const model = models.find((candidate) => candidate.key === modelKey) ?? models[0];
  const unchanged = server.running && server.model_key === modelKey && server.context === context && server.runtime === runtime;

  return (
    <div className="card form">
      <ServerHeading title="Generator" note="Generator" server={server} />
      <p className="hint">Writes the answer from the retrieved chunks. One model at a time; the GPU is much faster.</p>
      <label>
        <Explained note="Quantization">Model</Explained>
        <select value={modelKey} onChange={(e) => setModelKey(e.target.value)}>
          {models.map((candidate) => <option key={candidate.key} value={candidate.key}>{generatorOptionLabel(candidate, context, runtime)}</option>)}
        </select>
      </label>
      <label>
        <Explained note="Context window">Context window</Explained>
        <select value={context} onChange={(e) => setContext(Number(e.target.value))}>
          {state.options.generator_contexts.map((tokens) => <option key={tokens} value={tokens}>{tokens.toLocaleString()} tokens</option>)}
        </select>
      </label>
      <RuntimeField runtimes={state.options.runtimes} value={runtime} onChange={setRuntime} gpuLabel="GPU (CUDA)" />
      {model.notes && <p className="hint">{model.notes}</p>}
      <JobActivity jobs={state.jobs} matches={(job) => GENERATOR_JOBS.includes(job.kind)} />
      <div className="row">
        <button
          className="button button-primary"
          disabled={server.busy || unchanged}
          onClick={() => startGpu((force) => request("POST", "/servers/generator/start", { model_key: modelKey, runtime, context, force }))}
        >
          {server.running ? "Switch" : "Start"}
        </button>
        <button className="button" disabled={server.busy || !server.running} onClick={() => act(() => request("POST", "/servers/generator/stop"))}>
          Stop
        </button>
      </div>
    </div>
  );
}

function RerankerCard({ state, act, startGpu }: Props) {
  const server = state.servers.reranker;
  const models = state.options.reranker_models;
  const [modelKey, setModelKey] = useState(server.model_key ?? models[0].key);
  const [runtime, setRuntime] = useState(initialRuntime(server.runtime, state.options.runtimes));
  const model = models.find((candidate) => candidate.key === modelKey) ?? models[0];
  const unchanged = server.running && server.model_key === modelKey && server.runtime === runtime;

  return (
    <div className="card form">
      <ServerHeading title="Reranker" note="Reranking" server={server} />
      <p className="hint">Optional second pass on Search and Ask: re-orders a larger candidate pool. GPU is much faster.</p>
      <label>
        <Explained note="Cross-encoder">Model</Explained>
        <select value={modelKey} onChange={(e) => setModelKey(e.target.value)}>
          {models.map((candidate) => (
            <option key={candidate.key} value={candidate.key}>
              {candidate.label}{candidate.download_status === "downloaded" ? "" : ` — ${candidate.size_gb} GB download`}
            </option>
          ))}
        </select>
      </label>
      <RuntimeField runtimes={state.options.runtimes} value={runtime} onChange={setRuntime} gpuLabel={`GPU (CUDA) — ≈${model.vram_gb} GB VRAM`} />
      {model.notes && <p className="hint">{model.notes}</p>}
      <JobActivity jobs={state.jobs} matches={(job) => RERANKER_JOBS.includes(job.kind)} />
      <div className="row">
        <button
          className="button button-primary"
          disabled={server.busy || unchanged}
          onClick={() => startGpu((force) => request("POST", "/servers/reranker/start", { model_key: modelKey, runtime, force }))}
        >
          {server.running ? "Switch" : "Start"}
        </button>
        <button className="button" disabled={server.busy || !server.running} onClick={() => act(() => request("POST", "/servers/reranker/stop"))}>
          Stop
        </button>
      </div>
    </div>
  );
}
