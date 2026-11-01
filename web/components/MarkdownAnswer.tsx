import Markdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

const COMPONENTS: Components = {
  a: ({ node: _node, children, ...link }) => (
    <a {...link} target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
};

/**
 * A generator's answer rendered as GitHub-flavored Markdown: lists, emphasis, code and tables.
 * Images are dropped, so an answer can never make the browser fetch from another site; raw HTML is shown as text.
 */
export function MarkdownAnswer({ text }: { text: string }) {
  return (
    <div className="answer-text">
      <Markdown remarkPlugins={[remarkGfm]} disallowedElements={["img"]} components={COMPONENTS}>
        {text}
      </Markdown>
    </div>
  );
}
