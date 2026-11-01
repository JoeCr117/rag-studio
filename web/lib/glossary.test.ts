import { describe, expect, it } from "vitest";

import { obsidianLink } from "./glossary";

describe("obsidianLink", () => {
  it("opens the note by its vault path, encoding spaces and slashes", () => {
    expect(obsidianLink("Search/Search Methods/Hybrid search")).toBe(
      "obsidian://open?vault=RAGStudioVault&file=Search%2FSearch%20Methods%2FHybrid%20search",
    );
  });
});
