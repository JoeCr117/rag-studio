import type { AskResponse, ContextBudget, Database, GeneratorModelOption, ServerRole, ServerState, StudioState, Vram } from "./api";
import { searchBlocker } from "./explore";

const MIB_PER_GB = 1024;
const HEADROOM_GB = 1;

export type VramLevel = "ok" | "high" | "full";

export interface VramSummary {
  usedGb: number;
  totalGb: number;
  percent: number;
  level: VramLevel;
}

/** "full" means less than the 1 GB headroom is left: the point where the driver starts spilling into system RAM. */
export function vramSummary(vram: Vram): VramSummary {
  const usedGb = vram.used_mib / MIB_PER_GB;
  const totalGb = vram.total_mib / MIB_PER_GB;
  const percent = Math.round((vram.used_mib / vram.total_mib) * 100);
  const level: VramLevel = totalGb - usedGb < HEADROOM_GB ? "full" : percent >= 75 ? "high" : "ok";
  return { usedGb, totalGb, percent, level };
}

/** On the GPU, the VRAM estimate; on the CPU, the whole file plus the context's cache in system RAM. */
export function generatorOptionLabel(model: GeneratorModelOption, context: number, runtime: string): string {
  const cache = (model.kv_gb_per_8k * context) / 8192;
  const memory = runtime === "gpu" ? `≈${(model.vram_gb + cache).toFixed(1)} GB VRAM` : `≈${(model.size_gb + cache).toFixed(1)} GB RAM`;
  const download = model.download_status === "downloaded" ? "" : model.download_status === "downloading" ? ", downloading" : `, ${model.size_gb} GB download`;
  return `${model.label} — ${memory}${download}`;
}

/** The runtime a server card starts with: its last one while this install still offers it, else the GPU when there is one. */
export function initialRuntime(lastRuntime: string | null, runtimes: string[]): string {
  if (lastRuntime && runtimes.includes(lastRuntime)) return lastRuntime;
  return runtimes.includes("gpu") ? "gpu" : "cpu";
}

export function serverStatus(server: ServerState): "running" | "busy" | "stopped" {
  if (server.busy) return "busy";
  return server.running ? "running" : "stopped";
}

export function rerankBlocker(servers: StudioState["servers"]): string | null {
  return servers.reranker.running ? null : "Start the reranker on the Ask tab to rerank.";
}

export function askBlocker(database: Database, servers: Record<ServerRole, ServerState>): string | null {
  return searchBlocker(database) ?? (servers.generator.running ? null : "Start a generator above first.");
}

/** Why an answer asked to think came back without thinking, or without an answer; null when it went as asked. */
export function thinkingNotice(result: Pick<AskResponse, "answer" | "think" | "completion">): string | null {
  if (!result.think) return null;
  if (!result.completion.reasoning) {
    return "No thinking came back: this model's chat template has no thinking mode, so it answered directly.";
  }
  if (!result.answer.trim()) {
    return "The thinking used the whole output allowance before an answer was written. Ask again, or turn thinking off.";
  }
  return null;
}

/** Why the answer stops early: the output allowance ran out mid-answer. Thinking that left no answer is `thinkingNotice`'s. */
export function cutOffNotice(result: Pick<AskResponse, "answer" | "completion" | "context">): string | null {
  if (result.completion.finish_reason !== "length" || !result.answer.trim()) return null;
  return `The answer reached its ${result.context.output_allowance.toLocaleString("en-US")}-token output allowance and is cut off.`;
}

/** Says which passages were left out to fit the window; null when every passage found was used. */
export function leftOutNotice(context: ContextBudget): string | null {
  if (context.passages_left_out === 0) return null;
  const window = context.window.toLocaleString("en-US");
  return `The ${context.passages_left_out} lowest-ranked of ${context.passages_found} passages were left out to fit the ${window}-token context window. Ask for fewer results, or start the generator with a larger window.`;
}

/** Passage numbers the answer cites, as [n] or as a list such as [3, 4, 5]. */
export function citedPassages(answer: string): Set<number> {
  const brackets = [...answer.matchAll(/\[(\d+(?:\s*,\s*\d+)*)\]/g)];
  return new Set(brackets.flatMap((match) => match[1].split(",").map(Number)));
}
