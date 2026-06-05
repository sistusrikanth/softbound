import { useLayoutEffect, useRef, useState } from "react";
import type { BibleVersion, Character, Note, TimelineEntry } from "@/lib/types";
import { Icon } from "./icons";
import { Avatar, AskBar, NoteCompose, renderMarked } from "./shared";
import { CastControl } from "./characters";

export interface BibleViewProps {
  view: BibleVersion;
  versions: BibleVersion[];
  current: number;
  onGo: (i: number) => void;
  notes: Note[];
  activeNoteId: string | null;
  composing: { paraId: string; quote: string } | null;
  draft: string;
  setDraft: (v: string) => void;
  onWeave: () => void;
  onCancel: () => void;
  onTitleChange: (text: string) => void;
  onMouseUp: () => void;
  onMarkClick: (id: string) => void;
  onAsk: (text: string) => void;
  busy: boolean;
  timeline: TimelineEntry[];
  isHistorical: boolean;
  onApprove: () => void;
  characters: Character[];
  onOpenCast: () => void;
  castOpen: boolean;
  castDirty: boolean;
  isMobile?: boolean;
}

function Filmstrip({
  versions,
  current,
  onGo,
  onApprove,
  characters,
  onOpenCast,
  castOpen,
  castDirty,
}: Pick<BibleViewProps, "versions" | "current" | "onGo" | "onApprove" | "characters" | "onOpenCast" | "castOpen" | "castDirty">) {
  const railRef = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const el = railRef.current;
    if (!el) return;
    const card = el.children[current] as HTMLElement | undefined;
    card?.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
  }, [current, versions.length]);

  return (
    <div className="filmstrip">
      <CastControl characters={characters} onOpen={onOpenCast} active={castOpen} dirty={castDirty} />
      <div className="fs-divider" />
      <div className="fs-head">
        <Icon name="versions" size={15} /> versions
      </div>
      <button type="button" className="vstep" disabled={current === 0} onClick={() => onGo(current - 1)} aria-label="previous version">
        <Icon name="chevronLeft" size={18} />
      </button>
      <div className="fs-rail" ref={railRef}>
        {versions.map((v, i) => (
          <button key={v.id} type="button" className={"vcard" + (i === current ? " cur" : "")} onClick={() => onGo(i)}>
            <div className="vn">v{v.n}</div>
            <div className="vs">{v.changeSummary}</div>
            <div className="vt">{v.when}</div>
          </button>
        ))}
      </div>
      <button type="button" className="vstep" disabled={current === versions.length - 1} onClick={() => onGo(current + 1)} aria-label="next version">
        <Icon name="chevronRight" size={18} />
      </button>
      <div className="fs-advance">
        <button type="button" className="btn accent" onClick={onApprove}>
          shape the stories <Icon name="arrowRight" size={16} />
        </button>
      </div>
    </div>
  );
}

function ColumnAsk({ onAsk, busy }: { onAsk: (t: string) => void; busy: boolean }) {
  const [ask, setAsk] = useState("");
  const send = () => {
    if (ask.trim()) {
      onAsk(ask);
      setAsk("");
    }
  };
  return (
    <div className="ms-ask">
      <div className="ms-ask-head">
        <Icon name="spark" size={14} /> ask the co-author
      </div>
      <AskBar
        value={ask}
        onChange={setAsk}
        onSend={send}
        disabled={busy}
        placeholder='ask for a broader change — "make it warmer", "add a second creature"…'
      />
    </div>
  );
}

export function ManuscriptView(props: BibleViewProps) {
  const {
    view,
    versions,
    current,
    onGo,
    notes,
    activeNoteId,
    composing,
    draft,
    setDraft,
    onWeave,
    onCancel,
    onTitleChange,
    onMouseUp,
    onMarkClick,
    onAsk,
    busy,
    isHistorical,
    onApprove,
    characters,
    onOpenCast,
    castOpen,
    castDirty,
    isMobile,
  } = props;

  const pageRef = useRef<HTMLDivElement>(null);
  const paraRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const [tops, setTops] = useState<Record<string, number>>({});

  useLayoutEffect(() => {
    const measure = () => {
      const page = pageRef.current;
      if (!page) return;
      const base = page.getBoundingClientRect().top;
      const t: Record<string, number> = {};
      Object.entries(paraRefs.current).forEach(([id, el]) => {
        if (el) t[id] = el.getBoundingClientRect().top - base;
      });
      setTops(t);
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (pageRef.current) ro.observe(pageRef.current);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [view, notes.length, composing]);

  const items: { kind: string; id: string; paraId: string; data?: Note; top: number; placed?: number }[] = [];
  notes.forEach((n) => items.push({ kind: "note", id: n.id, paraId: n.paraId, data: n, top: tops[n.paraId] ?? 0 }));
  if (composing) items.push({ kind: "compose", id: "compose", paraId: composing.paraId, top: tops[composing.paraId] ?? 0 });
  items.sort((a, b) => a.top - b.top);
  let lastBottom = -999;
  items.forEach((it) => {
    const est = it.kind === "compose" ? 170 : 132;
    let top = Math.max(it.top, lastBottom + 14);
    it.placed = top;
    lastBottom = top + est;
  });

  return (
    <div className="ms">
      <div className="ms-scroll">
        <div className="ms-page" ref={pageRef} onMouseUp={onMouseUp}>
          <div className="ms-col">
            <div className="ms-vlabel">
              <span style={{ whiteSpace: "nowrap" }}>world bible · v{view.n}</span>
              <span className="dotline" />
              <span style={{ whiteSpace: "nowrap" }}>{isHistorical ? "viewing an earlier snapshot" : "live draft"}</span>
            </div>
            <h1
              className="ms-title"
              contentEditable={!isHistorical}
              suppressContentEditableWarning
              onBlur={(e) => onTitleChange(e.currentTarget.textContent || "")}
            >
              {view.title}
            </h1>
            <p className="ms-logline">{view.logline}</p>
            {view.paras.map((p) => {
              const pn = notes
                .filter((n) => n.paraId === p.id)
                .map((n) => ({ quote: n.quote, noteId: n.id, active: n.id === activeNoteId }));
              return (
                <div className={"ms-para" + (p.revised ? " revised-edge" : "")} key={p.id}>
                  {p.heading && <div className="ph">{p.heading}</div>}
                  <div className="ms-text" data-para={p.id} ref={(el) => { paraRefs.current[p.id] = el; }}>
                    {renderMarked(p.text, pn, onMarkClick)}
                  </div>
                </div>
              );
            })}
            {!isHistorical && <ColumnAsk onAsk={onAsk} busy={busy} />}
            {isHistorical && (
              <div className="ms-historical">
                <Icon name="versions" size={15} /> you're reading an earlier snapshot. return to the latest version to keep writing.
              </div>
            )}
            {isMobile && (notes.length > 0 || composing) && (
              <div className="ms-mobile-notes">
                <div className="ms-ask-head">
                  <Icon name="note" size={14} /> notes
                </div>
                {composing && (
                  <NoteCompose quote={composing.quote} value={draft} onChange={setDraft} onWeave={onWeave} onCancel={onCancel} busy={busy} />
                )}
                {notes.map((n) => (
                  <div key={n.id} className={"note-card flow" + (n.resolved ? " resolved" : "")}>
                    <div className="nq">"{n.quote}"</div>
                    <div className="nt">{n.text}</div>
                    <div className="nmeta">
                      {n.resolved ? (
                        <span className="rtag">
                          <Icon name="check" size={13} /> woven into v{n.resolvedIn}
                        </span>
                      ) : (
                        <span>
                          <Avatar /> &nbsp;you · just now
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          {!isMobile && (
            <div className="ms-margin">
              {items.map((it) =>
                it.kind === "note" && it.data ? (
                  <div
                    key={it.id}
                    className={"note-card" + (it.data.resolved ? " resolved" : "")}
                    style={{ top: it.placed }}
                  >
                    <div className="nq">"{it.data.quote}"</div>
                    <div className="nt">{it.data.text}</div>
                    <div className="nmeta">
                      {it.data.resolved ? (
                        <span className="rtag">
                          <Icon name="check" size={13} /> woven into v{it.data.resolvedIn}
                        </span>
                      ) : (
                        <span>
                          <Avatar /> &nbsp;you · just now
                        </span>
                      )}
                    </div>
                  </div>
                ) : (
                  <div key="compose" style={{ position: "absolute", top: it.placed, width: 280 }}>
                    {composing && (
                      <NoteCompose quote={composing.quote} value={draft} onChange={setDraft} onWeave={onWeave} onCancel={onCancel} busy={busy} />
                    )}
                  </div>
                ),
              )}
            </div>
          )}
        </div>
      </div>
      <Filmstrip
        versions={versions}
        current={current}
        onGo={onGo}
        onApprove={onApprove}
        characters={characters}
        onOpenCast={onOpenCast}
        castOpen={castOpen}
        castDirty={castDirty}
      />
    </div>
  );
}
