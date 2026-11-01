"use client";

import { useState, type FormEvent } from "react";

import type { DatabaseSettings, Options } from "@/lib/api";
import { modelOptionLabel } from "@/lib/explore";

import { Explained } from "./Explained";

interface Props {
  options: Options;
  initial?: DatabaseSettings;
  submitLabel: string;
  rebuildWarning?: boolean;
  onSubmit: (settings: DatabaseSettings) => Promise<boolean>;
  onCancel: () => void;
}

const VECTOR_FIELDS: Array<keyof DatabaseSettings> = [
  "engine", "embedding_model", "chunk_min_tokens", "chunk_max_tokens", "chunk_overlap_tokens",
];

export function DatabaseForm({ options, initial, submitLabel, rebuildWarning, onSubmit, onCancel }: Props) {
  const [settings, setSettings] = useState<DatabaseSettings>(initial ?? { name: "", ...options.defaults });
  const set = <K extends keyof DatabaseSettings>(field: K, value: DatabaseSettings[K]) =>
    setSettings((current) => ({ ...current, [field]: value }));
  const rebuilds = rebuildWarning && initial && VECTOR_FIELDS.some((field) => settings[field] !== initial[field]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (await onSubmit(settings)) onCancel();
  }

  return (
    <form className="card form" onSubmit={submit}>
      <label>
        Name
        <input value={settings.name} onChange={(e) => set("name", e.target.value)} required />
      </label>
      <div className="grid-2">
        <Select label="Engine" note="Vector engine" value={settings.engine} onChange={(v) => set("engine", v)} options={options.engines} />
        <Select
          label="Embedding model"
          note="Embedding model"
          value={settings.embedding_model}
          onChange={(v) => set("embedding_model", v)}
          options={options.embedding_models.map((model) => [model.key, modelOptionLabel(model)])}
        />
        <Select
          label="Embedder runs on"
          note="CPU and GPU inference"
          value={settings.embedder_runtime}
          onChange={(v) => set("embedder_runtime", v)}
          options={options.runtimes.map((runtime) => [runtime, runtime === "gpu" ? "GPU (CUDA)" : "CPU"])}
        />
        <Select
          label="Search mode"
          note="Hybrid search"
          value={settings.search_mode}
          onChange={(v) => set("search_mode", v)}
          options={options.search_modes.map((mode) => [mode, mode === "hybrid" ? "Hybrid (vector + keyword)" : "Vector only"])}
        />
        <NumberSelect label="Chunk min tokens" note="Chunk size" value={settings.chunk_min_tokens} onChange={(v) => set("chunk_min_tokens", v)} options={options.chunk_min_tokens} />
        <NumberSelect label="Chunk max tokens" note="Chunk size" value={settings.chunk_max_tokens} onChange={(v) => set("chunk_max_tokens", v)} options={options.chunk_max_tokens} />
        <NumberSelect label="Chunk overlap tokens" note="Chunk overlap" value={settings.chunk_overlap_tokens} onChange={(v) => set("chunk_overlap_tokens", v)} options={options.chunk_overlap_tokens} />
      </div>
      {rebuilds && (
        <p className="warn-text">
          These changes alter the vectors: the next Sync all <Explained note="Rebuild">rebuilds</Explained> this database.
        </p>
      )}
      <div className="row">
        <button className="button button-primary">{submitLabel}</button>
        <button type="button" className="link" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}

interface SelectProps {
  label: string;
  /** Vault note explaining the setting. */
  note: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<string | [string, string]>;
}

function Select(props: SelectProps) {
  return (
    <label>
      <Explained note={props.note}>{props.label}</Explained>
      <select value={props.value} onChange={(e) => props.onChange(e.target.value)}>
        {props.options.map((option) => {
          const [value, text] = Array.isArray(option) ? option : [option, option];
          return <option key={value} value={value}>{text}</option>;
        })}
      </select>
    </label>
  );
}

function NumberSelect(props: { label: string; note: string; value: number; onChange: (value: number) => void; options: number[] }) {
  return (
    <Select
      label={props.label}
      note={props.note}
      value={String(props.value)}
      onChange={(value) => props.onChange(Number(value))}
      options={props.options.map(String)}
    />
  );
}
