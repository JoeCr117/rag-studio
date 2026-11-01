import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { MarkdownAnswer } from "./MarkdownAnswer";

const html = (text: string) => renderToStaticMarkup(<MarkdownAnswer text={text} />);

describe("MarkdownAnswer", () => {
  it("renders lists and emphasis instead of showing the asterisks", () => {
    const rendered = html("Hybrid search:\n\n* **Merging:** by rank [1, 3].\n* **Pool:** 40 chunks [1].");
    expect(rendered).toContain("<ul>");
    expect(rendered).toContain("<strong>Merging:</strong> by rank [1, 3].");
    expect(rendered).not.toContain("**");
  });

  it("renders tables", () => {
    expect(html("| Engine | Fusion |\n|---|---|\n| Qdrant | RRF |")).toContain("<td>Qdrant</td>");
  });

  it("keeps adjacent citations as text", () => {
    expect(html("Both lists count [1][2].")).toContain("Both lists count [1][2].");
  });

  it("never loads images", () => {
    expect(html("![tracker](https://example.com/pixel.png)")).not.toContain("<img");
  });

  it("shows raw HTML as text instead of running it", () => {
    expect(html('<img src="https://example.com/x.png" onerror="alert(1)">')).not.toContain("<img");
  });

  it("opens links in a new tab", () => {
    expect(html("[docs](https://example.com)")).toContain('target="_blank" rel="noreferrer"');
  });
});
