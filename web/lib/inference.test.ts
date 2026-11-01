import { describe, expect, it } from "vitest";

import type { Database, GeneratorModelOption, ServerState, StudioState } from "./api";
import { askBlocker, citedPassages, cutOffNotice, generatorOptionLabel, initialRuntime, leftOutNotice, rerankBlocker, serverStatus, thinkingNotice, vramSummary } from "./inference";

const server = (overrides: Partial<ServerState> = {}): ServerState => ({
  model_key: null, runtime: null, context: null, running: false, busy: false, vram_gb: 0, ...overrides,
});
const servers = (generator: Partial<ServerState>, reranker: Partial<ServerState> = {}) =>
  ({ generator: server(generator), reranker: server(reranker) }) as StudioState["servers"];
const readyDatabase = { running: true, needs_rebuild: false, counts: { documents: 1, chunks: 2 } } as Database;

describe("vramSummary", () => {
  it("grades usage, with full meaning under 1 GB left", () => {
    expect(vramSummary({ used_mib: 2048, total_mib: 12288 }).level).toBe("ok");
    expect(vramSummary({ used_mib: 9500, total_mib: 12288 }).level).toBe("high");
    const full = vramSummary({ used_mib: 11800, total_mib: 12288 });
    expect(full.level).toBe("full");
    expect(full.percent).toBe(96);
  });
});

describe("generatorOptionLabel", () => {
  it("shows the memory estimate for the chosen context, runtime and any download", () => {
    const model = { label: "Qwen", vram_gb: 5, kv_gb_per_8k: 0.5, size_gb: 5.3, download_status: "missing" } as GeneratorModelOption;
    expect(generatorOptionLabel(model, 16384, "gpu")).toBe("Qwen — ≈6.0 GB VRAM, 5.3 GB download");
    expect(generatorOptionLabel({ ...model, download_status: "downloaded" }, 8192, "gpu")).toBe("Qwen — ≈5.5 GB VRAM");
    expect(generatorOptionLabel(model, 8192, "cpu")).toBe("Qwen — ≈5.8 GB RAM, 5.3 GB download");
  });
});

describe("initialRuntime", () => {
  it("keeps the last runtime while it is offered, else prefers the GPU", () => {
    expect(initialRuntime("cpu", ["cpu", "gpu"])).toBe("cpu");
    expect(initialRuntime(null, ["cpu", "gpu"])).toBe("gpu");
    expect(initialRuntime("gpu", ["cpu"])).toBe("cpu");
  });
});

describe("server readiness", () => {
  it("reports busy before running", () => {
    expect(serverStatus(server({ running: true, busy: true }))).toBe("busy");
    expect(serverStatus(server({ running: true }))).toBe("running");
  });

  it("blocks reranking and asking until their servers run", () => {
    expect(rerankBlocker(servers({}))).toMatch(/reranker/);
    expect(rerankBlocker(servers({}, { running: true }))).toBeNull();
    expect(askBlocker(readyDatabase, servers({}))).toMatch(/generator/);
    expect(askBlocker(readyDatabase, servers({ running: true }))).toBeNull();
  });
});

describe("context budget notices", () => {
  const context = { window: 8192, output_allowance: 1024, passages_found: 50, passages_used: 31, passages_left_out: 19 };
  const completion = (finish_reason: string) => ({
    text: "", reasoning: "", prompt_tokens: 0, completion_tokens: 0, prompt_ms: 0, generation_ms: 0, tokens_per_second: 0, finish_reason,
  });

  it("names the passages left out to fit the window", () => {
    expect(leftOutNotice(context)).toBe(
      "The 19 lowest-ranked of 50 passages were left out to fit the 8,192-token context window. " +
        "Ask for fewer results, or start the generator with a larger window.",
    );
    expect(leftOutNotice({ ...context, passages_used: 50, passages_left_out: 0 })).toBeNull();
  });

  it("warns only when an answer stopped at the output allowance", () => {
    expect(cutOffNotice({ answer: "Helen went", completion: completion("length"), context })).toMatch(/1,024-token output allowance/);
    expect(cutOffNotice({ answer: "Helen went home.", completion: completion("stop"), context })).toBeNull();
    expect(cutOffNotice({ answer: "", completion: completion("length"), context })).toBeNull();
  });
});

describe("thinkingNotice", () => {
  const ask = (think: boolean, reasoning: string, answer = "Twelve pens cost $8.") => ({
    answer, think,
    completion: { text: answer, reasoning, prompt_tokens: 0, completion_tokens: 0, prompt_ms: 0, generation_ms: 0, tokens_per_second: 0, finish_reason: "stop" },
  });

  it("says nothing when thinking was off or went as asked", () => {
    expect(thinkingNotice(ask(false, ""))).toBeNull();
    expect(thinkingNotice(ask(true, "3 pens = $2…"))).toBeNull();
  });

  it("explains a model that cannot think", () => {
    expect(thinkingNotice(ask(true, ""))).toMatch(/no thinking mode/);
  });

  it("explains thinking that left no room for the answer", () => {
    expect(thinkingNotice(ask(true, "long trace", "  "))).toMatch(/whole output allowance/);
  });
});

describe("citedPassages", () => {
  it("collects every [n] the answer cites", () => {
    expect([...citedPassages("Helen [1] reports to Raj [3][1].")]).toEqual([1, 3]);
    expect(citedPassages("I do not know.").size).toBe(0);
  });

  it("reads a bracketed list of passages", () => {
    expect([...citedPassages("There is one story: Grand Ted [3, 4, 5].")]).toEqual([3, 4, 5]);
    expect([...citedPassages("See [2,7] and [1].")]).toEqual([2, 7, 1]);
  });
});
