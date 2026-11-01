"use client";

import { useState } from "react";

import { VramMeter } from "@/components/VramMeter";
import type { StudioState } from "@/lib/api";

interface Props {
  state: StudioState | null;
  offline: boolean;
  terminalOpen: boolean;
  onToggleTerminal: () => void;
  onShutDown: () => Promise<void>;
}

export function StudioHeader({ state, offline, terminalOpen, onToggleTerminal, onShutDown }: Props) {
  const [confirmShutdown, setConfirmShutdown] = useState(false);
  const running = state?.jobs.find((job) => job.status === "running");
  const interruption = !running
    ? ""
    : running.progress?.unit === "bytes"
      ? " The running download will be lost: it starts again from the beginning next time."
      : " The running job will be interrupted.";

  return (
    <header className="header">
      <h1>RAG Studio</h1>
      <span className={offline ? "pill pill-bad" : "pill pill-good"}>{offline ? "API offline" : "API connected"}</span>
      {state && <VramMeter vram={state.vram} gpuAvailable={state.gpu_available} />}
      <div className="header-actions">
        <button className="button" aria-pressed={terminalOpen} onClick={onToggleTerminal}>
          {terminalOpen ? "Hide terminal" : "Show terminal"}
        </button>
        {confirmShutdown ? (
          <>
            <button className="button button-danger" onClick={() => onShutDown().finally(() => setConfirmShutdown(false))}>
              Confirm shut down
            </button>
            <button className="link" onClick={() => setConfirmShutdown(false)}>Cancel</button>
          </>
        ) : (
          <button
            className="button"
            disabled={offline}
            title={`Stops every RAG Studio container, including the generator and embedders. Data and models are kept.${interruption}`}
            onClick={() => setConfirmShutdown(true)}
          >
            Shut down
          </button>
        )}
      </div>
    </header>
  );
}
