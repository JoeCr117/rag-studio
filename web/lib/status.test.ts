import { describe, expect, it } from "vitest";

import type { Database, Source } from "./api";
import { needsSync, syncTargets, unassignedDatabases, unassignedSources } from "./status";

const source = (id: number, databaseIds: number[] = []): Source => ({
  id, name: `s${id}`, host_path: "", include_patterns: "", exclude_patterns: "", found: true, file_count: 1,
  scanned_at: null, scan_error: "",
  assignments: databaseIds.map((database_id) => ({ database_id, database_name: `d${database_id}`, status: "synced" })),
});

const database = (id: number, running: boolean, assigned: Array<[number, boolean]>): Database => ({
  id, name: `d${id}`, engine: "pgvector", embedding_model: "m", embedder_runtime: "cpu", chunk_min_tokens: 150,
  chunk_max_tokens: 400, chunk_overlap_tokens: 40, search_mode: "hybrid", embedder: "e", running, ready: true,
  needs_rebuild: false, busy: false, counts: null, warnings: [],
  assignments: assigned.map(([source_id, connected]) => ({
    source_id, source_name: `s${source_id}`, connected, status: "synced", synced_at: null,
  })),
});

describe("status helpers", () => {
  it("asks for a sync only when content differs or was never ingested", () => {
    expect(needsSync("changed")).toBe(true);
    expect(needsSync("never_synced")).toBe(true);
    expect(needsSync("synced")).toBe(false);
    expect(needsSync("disconnected")).toBe(false);
  });

  it("offers only sources and databases that are not already paired", () => {
    expect(unassignedSources([source(1), source(2)], database(9, true, [[1, true]])).map((s) => s.id)).toEqual([2]);
    expect(unassignedDatabases([database(8, true, []), database(9, true, [])], source(1, [9])).map((d) => d.id)).toEqual([8]);
  });

  it("pushes a source only into running databases it is connected to", () => {
    const databases = [database(1, true, [[5, true]]), database(2, false, [[5, true]]), database(3, true, [[5, false]])];
    expect(syncTargets(databases, source(5)).map((d) => d.id)).toEqual([1]);
  });
});
