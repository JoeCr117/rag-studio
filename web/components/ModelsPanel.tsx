"use client";

import { useState, type ReactNode } from "react";

import { request, type BuiltInModel, type DownloadStatus, type Job, type StudioState, type VolumeLocation } from "@/lib/api";
import type { Act } from "@/lib/useStudioState";

import { Explained } from "./Explained";
import { JobActivity } from "./JobActivity";

const STATUS_CLASS = { downloaded: "pill-good", downloading: "pill-busy", missing: "" } as const;

interface ModelCardProps {
  model: { key: string; label: string; repo: string; file: string; size_gb: number; notes: string; download_status: DownloadStatus };
  location: VolumeLocation;
  tokenizer?: VolumeLocation;
  jobs: Job[];
  act: Act;
  chips: Chip[];
  usedBy?: ReactNode;
}

interface Chip {
  text: string;
  /** Vault note explaining what the chip says. */
  note: string;
}

function VolumePaths({ location }: { location: VolumeLocation }) {
  return (
    <>
      <dt>In containers</dt>
      <dd><code>{location.container_path}</code></dd>
      <dt>On Windows</dt>
      <dd><code>{location.windows_path}</code></dd>
    </>
  );
}

function DeleteModelButton({ model, act }: { model: ModelCardProps["model"]; act: Act }) {
  const [confirming, setConfirming] = useState(false);
  if (!confirming) {
    return (
      <button
        className="button"
        title="Removes the file from the models volume. It downloads again the next time something starts it."
        onClick={() => setConfirming(true)}
      >
        Delete
      </button>
    );
  }
  return (
    <>
      <button
        className="button button-danger"
        onClick={() => act(() => request("DELETE", `/models/${model.key}`)).finally(() => setConfirming(false))}
      >
        Confirm delete {model.size_gb} GB
      </button>
      <button className="link" onClick={() => setConfirming(false)}>Cancel</button>
    </>
  );
}

function ModelCard({ model, location, tokenizer, jobs, act, chips, usedBy }: ModelCardProps) {
  return (
    <div className="card">
      <div className="row">
        <strong><Explained note="Model file names" detail={model.file}>{model.label}</Explained></strong>
        <span className={`pill ${STATUS_CLASS[model.download_status]}`}>{model.download_status}</span>
        <Explained note="Docker volume" asChild><span className="pill">models volume</span></Explained>
        <span className="spacer" />
        {model.download_status === "downloaded" ? (
          <DeleteModelButton model={model} act={act} />
        ) : (
          <button
            className="button"
            disabled={model.download_status === "downloading"}
            onClick={() => act(() => request("POST", `/models/${model.key}/download`))}
          >
            Download {model.size_gb} GB
          </button>
        )}
      </div>
      <div className="chips">
        {chips.map((chip) => (
          <Explained key={chip.text} note={chip.note} asChild><span className="pill">{chip.text}</span></Explained>
        ))}
      </div>
      {model.notes && <p className="hint">{model.notes}</p>}
      <JobActivity jobs={jobs} matches={(job) => job.model_key === model.key} />
      <dl className="storage">
        <dt><Explained note="Hugging Face">Pulled from</Explained></dt>
        <dd><a href={location.source_url} target="_blank" rel="noreferrer">Hugging Face: {model.repo}</a></dd>
        <VolumePaths location={location} />
        {tokenizer && (
          <>
            <dt><Explained note="Tokenizer">Tokenizer</Explained></dt>
            <dd>
              <a href={tokenizer.source_url} target="_blank" rel="noreferrer">{tokenizer.source_url.replace("https://", "")}</a>
              {tokenizer.present ? "" : " (fetched on the first sync that uses this model)"}
            </dd>
            <VolumePaths location={tokenizer} />
          </>
        )}
      </dl>
      {usedBy}
    </div>
  );
}

function BuiltInCard({ model }: { model: BuiltInModel }) {
  return (
    <div className="card">
      <div className="row">
        <strong><Explained note={model.note}>{model.label}</Explained></strong>
        <Explained note="Docker image" asChild><span className="pill pill-accent">Inside image</span></Explained>
      </div>
      <p className="hint">{model.used_for}. {model.notes}</p>
      <dl className="storage">
        <dt>Image</dt>
        <dd><code>{model.image}</code> (service <code>{model.service}</code>)</dd>
        <dt>Path in image</dt>
        <dd>{model.image_paths.map((path) => <code key={path} className="path">{path}</code>)}</dd>
      </dl>
    </div>
  );
}

export function ModelsPanel({ state, act }: { state: StudioState; act: Act }) {
  const { embedding_models, generator_models, reranker_models } = state.options;
  const { volume, files, tokenizers, built_in } = state.model_locations;
  return (
    <section className="panel explore">
      <div className="card">
        <strong><Explained note="Docker volume">Where models live</Explained></strong>
        <p className="hint">
          Downloaded models are <Explained note="GGUF">GGUF files</Explained> in the Docker volume <code>rag-studio_models</code>, not inside any image. Anything
          missing downloads when first started; download here to have it ready, or delete it here to free the space. The
          llama.cpp containers mount this volume read-only.
        </p>
        <dl className="storage">
          <dt>In containers</dt>
          <dd><code>{volume.container_path}</code></dd>
          <dt>On Windows</dt>
          <dd><code>{volume.windows_path}</code> (paste into Explorer while Docker Desktop runs)</dd>
        </dl>
      </div>
      <h2><Explained note="Embedding model">Embedding models</Explained></h2>
      {embedding_models.map((model) => {
        const users = state.databases.filter((database) => database.embedding_model === model.key);
        return (
          <ModelCard
            key={model.key}
            model={model}
            location={files[model.key]}
            tokenizer={tokenizers[model.key]}
            jobs={state.jobs}
            act={act}
            chips={[
              model.dimensions > 2000
                ? { text: `${model.dimensions} dims (halfvec in pgvector)`, note: "halfvec" }
                : { text: `${model.dimensions} dims`, note: "Dimensions" },
              { text: `${model.pooling} pooling`, note: "Pooling" },
              { text: model.query_prefix ? "query prefix" : "no query prefix", note: "Instruction prefix" },
              ...(model.document_prefix ? [{ text: "document prefix", note: "Instruction prefix" }] : []),
            ]}
            usedBy={<p className="meta">Used by: {users.length ? users.map((database) => database.name).join(", ") : "no databases"}</p>}
          />
        );
      })}
      <h2><Explained note="Generator">Generators</Explained></h2>
      {generator_models.map((model) => (
        <ModelCard
          key={model.key}
          model={model}
          location={files[model.key]}
          jobs={state.jobs}
          act={act}
          chips={[
            { text: `≈${model.vram_estimate_gb} GB VRAM at 8k context`, note: "KV cache" },
            ...(model.cpu_moe_layers ? [{ text: `${model.cpu_moe_layers} expert layers in system RAM`, note: "Mixture of Experts" }] : []),
          ]}
        />
      ))}
      <h2><Explained note="Cross-encoder">Rerankers</Explained></h2>
      {reranker_models.map((model) => (
        <ModelCard
          key={model.key}
          model={model}
          location={files[model.key]}
          jobs={state.jobs}
          act={act}
          chips={[{ text: `≈${model.vram_gb} GB VRAM on GPU`, note: "VRAM" }]}
        />
      ))}
      <h2><Explained note="Docker image">Built into images</Explained></h2>
      <p className="hint">Keyword scorers that ship inside a service&apos;s image. Nothing is downloaded and nothing is stored in the models volume.</p>
      {built_in.map((model) => <BuiltInCard key={model.key} model={model} />)}
    </section>
  );
}
