import type { Vram } from "@/lib/api";
import { vramSummary } from "@/lib/inference";

import { Explained } from "./Explained";

/** Live use of the whole GPU, every process included (the desktop and other apps too); "CPU only" without one. */
export function VramMeter({ vram, gpuAvailable }: { vram: Vram | null; gpuAvailable: boolean }) {
  if (!gpuAvailable) {
    return (
      <Explained note="CPU and GPU inference" detail="start.ps1 found no NVIDIA GPU, so every model runs on the CPU." asChild>
        <span className="pill">CPU only</span>
      </Explained>
    );
  }
  if (!vram) {
    return (
      <Explained note="VRAM" detail="nvidia-smi is not available in the API container, so use cannot be read." asChild>
        <span className="pill">VRAM n/a</span>
      </Explained>
    );
  }
  const summary = vramSummary(vram);
  return (
    <Explained note="VRAM" detail={`${summary.percent}% of the GPU's memory in use, by every process on the machine.`} asChild>
      <span className={`vram vram-${summary.level}`}>
        <span className="vram-label">VRAM {summary.usedGb.toFixed(1)} / {summary.totalGb.toFixed(1)} GB</span>
        <span className="vram-bar"><span style={{ width: `${summary.percent}%` }} /></span>
      </span>
    </Explained>
  );
}
