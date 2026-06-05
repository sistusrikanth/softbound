import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { Note, TimelineEntry } from "@/lib/types";
import { Icon } from "./icons";
import { Avatar, NoteCompose, renderMarked } from "./shared";
import type { BibleViewProps } from "./ManuscriptView";
import { CastControl } from "./characters";

function CoauthorRail({ timeline, onAsk, busy }: { timeline: TimelineEntry[]; onAsk: (t: string) => void; busy: boolean }) {
  const [ask, setAsk] = useState("");
  const logRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [timeline.length]);

  const KIND: Record<string, { k: string; ai: boolean; icon: string }> = {
    seed: { k: "you seeded", ai: false, icon: "feather" },
    ask: { k: "you asked", ai: false, icon: "pen" },
    note: { k: "you noted", ai: false, icon: "note" },
    "ai-draft": { k: "co-author", ai: true, icon: "spark" },
    "ai-revise": { k: "co-author", ai: true, icon: "spark" },
  };

  return (
    <div className="st-rail">
      <div className="st-rail-head">
        <div className="st-coauthor">
          <span className="ava">
            <Icon name="spark" size={19} />
          </span>
          <div>
            <div className="nm">the co-author</div>
            <div className="rl">writes with you</div>
          </div>
        </div>
      </div>
      <div className="st-log" ref={logRef}>
        {timeline.map((e, i) => {
          const meta = KIND[e.kind] || KIND.note;
          return (
            <div className={"logitem" + (meta.ai ? " ai" : "")} key={i}>
              <span className="dot">
                <Icon name={meta.icon} size={14} />
              </span>
              <div>
                <div className="lk">
                  {meta.k}
                  {e.vN ? ` · v${e.vN}` : ""}
                </div>
                <div className="lt">{e.text}</div>
                {e.quote && <div className="lq">"{e.quote}"</div>}
              </div>
            </div>
          );
        })}
        {busy && (
          <div className="logitem ai">
            <span className="dot">
              <Icon name="spark" size={14} />
            </span>
            <div>
              <div className="lk">co-author</div>
              <div className="lt" style={{ color: "var(--fg-muted)", fontStyle: "italic", fontFamily: "var(--font-serif)" }}>
                thinking, slowly…
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="st-compose">
        <div className="askbar">
          <span className="sp">
            <Icon name="spark" size={18} />
          </span>
          <input
            value={ask}
            placeholder="ask for a change…"
            onChange={(e) => setAsk(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && ask.trim()) {
                onAsk(ask);
                setAsk("");
              }
            }}
          />
          <button
            type="button"
            className="go"
            disabled={!ask.trim() || busy}
            onClick={() => {
              onAsk(ask);
              setAsk("");
            }}
          >
            <Icon name="send" size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

function Spine({
  versions,
  current,
  onGo,
  onApprove,
  characters,
  onOpenCast,
  castOpen,
  castDirty,
}: Pick<BibleViewProps, "versions" | "current" | "onGo" | "onApprove" | "characters" | "onOpenCast" | "castOpen" | "castDirty">) {
  const v = versions[current];
  return (
    <div className="st-spine">
      <div className="spine-row">
        <CastControl characters={characters} onOpen={onOpenCast} active={castOpen} dirty={castDirty} />
        <div className="fs-divider" />
        <div className="spine-title">
          <Icon name="layers" size={15} /> snapshots
        </div>
        <div className="spine-track">
          {versions.map((ver, i) => (
            <button key={ver.id} type="button" className={"pageedge" + (i === current ? " cur" : "")} onClick={() => onGo(i)} title={ver.changeSummary}>
              <div className="pn">v{ver.n}</div>
              <div className="ps">{ver.changeSummary}</div>
            </button>
          ))}
        </div>
        <div className="spine-dial">
          <button type="button" className="vstep" disabled={current === 0} onClick={() => onGo(current - 1)}>
            <Icon name="chevronLeft" size={18} />
          </button>
          <div className="spine-now">
            v{v.n} of {versions.length}
          </div>
          <button type="button" className="vstep" disabled={current === versions.length - 1} onClick={() => onGo(current + 1)}>
            <Icon name="chevronRight" size={18} />
          </button>
        </div>
        <div className="fs-advance">
          <button type="button" className="btn accent" onClick={onApprove}>
            shape the stories <Icon name="arrowRight" size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

export function StudioView(props: BibleViewProps) {
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
    timeline,
    isHistorical,
    onApprove,
    characters,
    onOpenCast,
    castOpen,
    castDirty,
  } = props;

  const canvasRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const paraRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const [geo, setGeo] = useState<{ stickies: Sticky[]; paths: Path[]; w: number; h: number }>({
    stickies: [],
    paths: [],
    w: 0,
    h: 0,
  });

  type Sticky = Note & { compose?: boolean; x: number; top: number; anchorY: number; anchorX: number };
  type Path = { d: string; active: boolean };

  useLayoutEffect(() => {
    const measure = () => {
      const canvas = canvasRef.current;
      const card = cardRef.current;
      if (!canvas || !card) return;
      const cb = canvas.getBoundingClientRect();
      const card_b = card.getBoundingClientRect();
      const cardRight = card_b.right - cb.left;
      const items: Sticky[] = [];
      (composing
        ? [...notes.map((n) => ({ ...n })), { id: "__compose", paraId: composing.paraId, quote: composing.quote, text: "", compose: true } as Sticky]
        : notes
      ).forEach((n) => {
        const el = paraRefs.current[n.paraId];
        if (!el) return;
        const r = el.getBoundingClientRect();
        items.push({
          ...n,
          anchorY: (r.top + r.bottom) / 2 - cb.top,
          anchorX: cardRight,
          x: 0,
          top: 0,
        });
      });
      items.sort((a, b) => a.anchorY - b.anchorY);
      const stickyX = cardRight + 34;
      let lastBottom = -999;
      const stickies = items.map((it) => {
        const est = it.compose ? 176 : 128;
        let top = Math.max(it.anchorY - 22, lastBottom + 16);
        lastBottom = top + est;
        return { ...it, x: stickyX, top };
      });
      const paths = stickies.map((s) => {
        const x1 = s.anchorX;
        const y1 = s.anchorY;
        const x2 = s.x;
        const y2 = s.top + 22;
        return { d: `M ${x1} ${y1} C ${x1 + 28} ${y1}, ${x2 - 26} ${y2}, ${x2} ${y2}`, active: s.id === activeNoteId };
      });
      setGeo({ stickies, paths, w: canvas.scrollWidth, h: canvas.scrollHeight });
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (canvasRef.current) ro.observe(canvasRef.current);
    if (cardRef.current) ro.observe(cardRef.current);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [view, notes.length, composing, activeNoteId, current]);

  return (
    <div className="st">
      <CoauthorRail timeline={timeline} onAsk={onAsk} busy={busy} />
      <div className="st-canvas" ref={canvasRef}>
        <div className="st-canvas-inner" onMouseUp={onMouseUp}>
          <svg className="st-connectors" width={geo.w} height={geo.h}>
            {geo.paths.map((p, i) => (
              <path
                key={i}
                d={p.d}
                fill="none"
                stroke={p.active ? "var(--accent-deep)" : "var(--accent)"}
                strokeWidth={p.active ? 1.6 : 1.1}
                strokeDasharray="1 5"
                strokeLinecap="round"
                opacity={p.active ? 0.9 : 0.55}
              />
            ))}
          </svg>

          <div className="st-card" ref={cardRef}>
            <div className="st-vlabel">
              world bible · v{view.n}
              {isHistorical ? " · earlier snapshot" : ""}
            </div>
            <h1
              className="st-title"
              contentEditable={!isHistorical}
              suppressContentEditableWarning
              onBlur={(e) => onTitleChange(e.currentTarget.textContent || "")}
            >
              {view.title}
            </h1>
            <p className="st-logline">{view.logline}</p>
            {view.paras.map((p) => {
              const pn = notes
                .filter((n) => n.paraId === p.id)
                .map((n) => ({ quote: n.quote, noteId: n.id, active: n.id === activeNoteId }));
              return (
                <div className={"st-para" + (p.revised ? " revised-edge" : "")} key={p.id}>
                  {p.heading && <div className="ph">{p.heading}</div>}
                  <div className="st-text" data-para={p.id} ref={(el) => { paraRefs.current[p.id] = el; }}>
                    {renderMarked(p.text, pn, onMarkClick)}
                  </div>
                </div>
              );
            })}
          </div>

          {geo.stickies.map((s) =>
            s.compose ? (
              <div
                key="compose"
                className="st-sticky"
                style={{ left: s.x, top: s.top, width: 256, padding: 0, border: "none", boxShadow: "none", background: "transparent" }}
              >
                {composing && (
                  <NoteCompose quote={composing.quote} value={draft} onChange={setDraft} onWeave={onWeave} onCancel={onCancel} busy={busy} />
                )}
              </div>
            ) : (
              <div key={s.id} className={"st-sticky" + (s.resolved ? " resolved" : "")} style={{ left: s.x, top: s.top }}>
                <div className="nq">"{s.quote}"</div>
                <div className="nt">{s.text}</div>
                <div className="nmeta">
                  {s.resolved ? (
                    <span style={{ color: "var(--success)", display: "inline-flex", alignItems: "center", gap: 4 }}>
                      <Icon name="check" size={12} /> woven into v{s.resolvedIn}
                    </span>
                  ) : (
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                      <Avatar size={16} /> you · just now
                    </span>
                  )}
                </div>
              </div>
            ),
          )}
        </div>
      </div>
      <Spine
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
