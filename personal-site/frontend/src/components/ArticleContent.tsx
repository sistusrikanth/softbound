import ReactMarkdown from "react-markdown";
import ExcalidrawEmbed from "./ExcalidrawEmbed";

const EXCALIDRAW_RE = /<!--\s*excalidraw:(.+?)\s*-->/g;

export default function ArticleContent({ content }: { content: string }) {
  const parts: Array<{ type: "markdown" | "excalidraw"; value: string }> = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  const re = new RegExp(EXCALIDRAW_RE.source, "g");
  while ((match = re.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "markdown", value: content.slice(lastIndex, match.index) });
    }
    parts.push({ type: "excalidraw", value: match[1].trim() });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    parts.push({ type: "markdown", value: content.slice(lastIndex) });
  }

  if (parts.length === 0) {
    parts.push({ type: "markdown", value: content });
  }

  return (
    <>
      {parts.map((part, i) =>
        part.type === "excalidraw" ? (
          <ExcalidrawEmbed key={`ex-${i}`} src={part.value} />
        ) : (
          <div key={`md-${i}`} className="markdown-body">
            <ReactMarkdown>{part.value}</ReactMarkdown>
          </div>
        ),
      )}
    </>
  );
}
