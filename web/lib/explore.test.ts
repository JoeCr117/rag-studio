import { describe, expect, it } from "vitest";

import type { Database, EmbeddingModelOption, SearchHit } from "./api";
import { modelOptionLabel, pickDatabase, rankSummary, searchBlocker, vectorPreviewText } from "./explore";

const database = (id: number, overrides: Partial<Database> = {}) =>
  ({ id, running: false, needs_rebuild: false, counts: { documents: 1, chunks: 3 }, ...overrides }) as Database;

describe("pickDatabase", () => {
  it("keeps the chosen database while it exists", () => {
    expect(pickDatabase([database(1), database(2)], 2)?.id).toBe(2);
  });

  it("falls back to a running database that needs no rebuild", () => {
    const databases = [database(1), database(2, { running: true, needs_rebuild: true }), database(3, { running: true })];
    expect(pickDatabase(databases, 9)?.id).toBe(3);
  });

  it("returns null when there are no databases", () => {
    expect(pickDatabase([], null)).toBeNull();
  });
});

describe("searchBlocker", () => {
  it("explains stopped, stale and empty databases", () => {
    expect(searchBlocker(database(1))).toMatch(/^Start/);
    expect(searchBlocker(database(1, { running: true, needs_rebuild: true }))).toMatch(/rebuild/);
    expect(searchBlocker(database(1, { running: true, counts: { documents: 0, chunks: 0 } }))).toMatch(/^Nothing/);
    expect(searchBlocker(database(1, { running: true }))).toBeNull();
  });
});

describe("labels", () => {
  it("names which ranking found a hit", () => {
    expect(rankSummary({ semantic_rank: 2, keyword_rank: null } as SearchHit)).toBe("vector #2 · keyword —");
  });

  it("flags models that still need downloading", () => {
    const model = { label: "Big", size_gb: 2.5 } as EmbeddingModelOption;
    expect(modelOptionLabel({ ...model, download_status: "downloaded" })).toBe("Big");
    expect(modelOptionLabel({ ...model, download_status: "missing" })).toBe("Big — 2.5 GB download on Start");
  });

  it("shortens long vectors", () => {
    expect(vectorPreviewText([0.5, -0.25], 2)).toBe("[0.5000, -0.2500]");
    expect(vectorPreviewText([0.5, -0.25], 1024)).toBe("[0.5000, -0.2500, … 1022 more]");
  });
});
