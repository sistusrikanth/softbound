import { useEffect, useRef } from "react";
import { Icon } from "./icons";

export function renderMarked(
  text: string,
  marks: { quote: string; noteId: string; active?: boolean }[] = [],
  onClick?: (id: string) => void,
) {
  const valid = marks.filter((m) => m.quote && m.quote.trim());
  if (!valid.length) return text;
  const ranges: { start: number; end: number; quote: string; noteId: string; active?: boolean }[] = [];
  valid.forEach((m) => {
    const idx = text.indexOf(m.quote);
    if (idx >= 0) ranges.push({ start: idx, end: idx + m.quote.length, ...m });
  });
  ranges.sort((a, b) => a.start - b.start);
  const out: (string | JSX.Element)[] = [];
  let cursor = 0;
  let key = 0;
  ranges.forEach((r) => {
    if (r.start < cursor) return;
    if (r.start > cursor) out.push(text.slice(cursor, r.start));
    out.push(
      <mark
        key={key++}
        className={r.active ? "activeNote" : ""}
        onMouseDown={(e) => e.stopPropagation()}
        onClick={(e) => {
          e.stopPropagation();
          onClick?.(r.noteId);
        }}
      >
        {text.slice(r.start, r.end)}
      </mark>,
    );
    cursor = r.end;
  });
  if (cursor < text.length) out.push(text.slice(cursor));
  return out;
}

export function Avatar({ size = 18 }: { size?: number }) {
  return (
    <span className="av" style={{ width: size, height: size }}>
      <Icon name="sparkSmall" size={size * 0.62} />
    </span>
  );
}

export function NoteCompose({
  quote,
  value,
  onChange,
  onWeave,
  onCancel,
  busy,
}: {
  quote: string;
  value: string;
  onChange: (v: string) => void;
  onWeave: () => void;
  onCancel: () => void;
  busy?: boolean;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);

  return (
    <div className="compose">
      <div className="cq">"{quote}"</div>
      <textarea
        ref={ref}
        value={value}
        placeholder="tell the co-author what to change…"
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onWeave();
          if (e.key === "Escape") onCancel();
        }}
      />
      <div className="crow">
        <button type="button" className="btn ghost sm" onMouseDown={(e) => e.preventDefault()} onClick={onCancel}>
          cancel
        </button>
        <button type="button" className="btn accent sm" disabled={!value.trim() || busy} onClick={onWeave}>
          <Icon name="spark" size={15} /> {busy ? "weaving…" : "weave in"}
        </button>
      </div>
    </div>
  );
}

export function AskBar({
  value,
  onChange,
  onSend,
  disabled,
  placeholder,
  icon = "feather",
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
  placeholder: string;
  icon?: string;
}) {
  return (
    <div className="askbar">
      <span className="sp">
        <Icon name={icon} size={17} />
      </span>
      <input
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") onSend();
        }}
      />
      <button type="button" className="go" disabled={!value.trim() || disabled} onClick={onSend}>
        <Icon name="send" size={16} />
      </button>
    </div>
  );
}
