"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, request, VRAM_WARNING, type StudioState } from "./api";
import { stopFolderPicker } from "./folderPicker";

const POLL_MS = 1000;

/** Sends a GPU start; `force` skips the VRAM check. */
export type GpuStart = (force: boolean) => Promise<unknown>;

/** "stopping" once the shutdown was accepted; "stopped" when the API no longer answers. */
export type ShutdownPhase = "stopping" | "stopped" | null;

export interface VramPrompt {
  message: string;
  send: GpuStart;
}

/** The whole page state, refreshed every second; `act` runs an API call, then refreshes and reports errors. */
export function useStudioState() {
  const [state, setState] = useState<StudioState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [vramPrompt, setVramPrompt] = useState<VramPrompt | null>(null);
  const [shutdownPhase, setShutdownPhase] = useState<ShutdownPhase>(null);

  const refresh = useCallback(async () => {
    try {
      setState(await request<StudioState>("GET", "/state"));
      setOffline(false);
    } catch {
      setOffline(true);
      setShutdownPhase((phase) => (phase === "stopping" ? "stopped" : phase));
    }
  }, []);

  useEffect(() => {
    if (shutdownPhase === "stopped") return;
    // oxlint-disable-next-line react/set-state-in-effect -- polling the API is syncing with an external system; state is set after the fetch
    refresh();
    const timer = setInterval(refresh, POLL_MS);
    return () => clearInterval(timer);
  }, [refresh, shutdownPhase]);

  const act = useCallback(
    async (action: () => Promise<unknown>): Promise<boolean> => {
      try {
        await action();
        setError(null);
        return true;
      } catch (failure) {
        setError(failure instanceof Error ? failure.message : String(failure));
        return false;
      } finally {
        refresh();
      }
    },
    // oxlint-disable-next-line react/memo-dependencies -- React's exhaustive-deps rule requires listing refresh
    [refresh],
  );

  /** Starts something on the GPU; when the API warns it may not fit, holds it for the Start anyway banner. */
  const startGpu = useCallback(
    (send: GpuStart) =>
      act(async () => {
        try {
          await send(false);
        } catch (failure) {
          if (failure instanceof ApiError && failure.status === VRAM_WARNING) {
            setVramPrompt({ message: failure.message, send });
            return;
          }
          throw failure;
        }
      }),
    [act],
  );

  const confirmVram = useCallback(() => {
    if (!vramPrompt) return;
    setVramPrompt(null);
    act(() => vramPrompt.send(true));
  }, [act, vramPrompt]);

  const shutDown = useCallback(async () => {
    if (!(await act(() => request("POST", "/shutdown")))) return;
    setShutdownPhase("stopping");
    await stopFolderPicker();
  }, [act]);

  return {
    state, error, offline, act, startGpu, vramPrompt, confirmVram, shutdownPhase, shutDown,
    clearError: () => setError(null),
    dismissVram: () => setVramPrompt(null),
  };
}

export type Act = ReturnType<typeof useStudioState>["act"];
export type StartGpu = ReturnType<typeof useStudioState>["startGpu"];
