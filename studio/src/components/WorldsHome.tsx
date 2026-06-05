import { useState } from "react";
import type { World, WorldTint } from "@/lib/types";
import { BookMark, Icon } from "./icons";

const COVER_TINT: Record<WorldTint, [string, string]> = {
  clay: ["#C89B7B", "#A87A5B"],
  sage: ["#9DAE93", "#5A6B52"],
  sky: ["#9DB2BD", "#6E8794"],
  honey: ["#D8B06A", "#B4904A"],
  rose: ["#D9A59B", "#B97A6E"],
};

function StageDots({ world }: { world: World }) {
  const stages = [
    { k: "bible", done: (world.versions || []).length > 0 },
    { k: "style", done: !!world.style },
    { k: "stories", done: (world.stories || []).some((s) => !s.proposed) },
    { k: "flow", done: !!world.flowStarted },
  ];
  return (
    <div className="wc-stages">
      {stages.map((s) => (
        <span key={s.k} className={"wc-dot" + (s.done ? " done" : "")} title={s.k} />
      ))}
    </div>
  );
}

function WorldCover({ world }: { world: World }) {
  const tint = world.tint || "clay";
  const pair = COVER_TINT[tint] || COVER_TINT.clay;
  const styleName = world.style ? world.style.name : null;
  return (
    <div className="wc-cover" style={{ background: pair[0] }}>
      <svg className="wc-cover-art" viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
        <rect width="320" height="200" fill={pair[0]} />
        <circle cx="232" cy="62" r="34" fill="#F4ECE0" opacity="0.5" />
        <path d="M0 150 Q 80 110 160 140 T 320 132 V200 H0 Z" fill={pair[1]} opacity="0.55" />
        <path d="M0 172 Q 90 142 180 166 T 320 158 V200 H0 Z" fill={pair[1]} opacity="0.8" />
      </svg>
      <div className="wc-cover-mark" style={{ color: "#F4ECE0" }}>
        <BookMark size={30} />
      </div>
      {styleName && (
        <span className="wc-style">
          <Icon name="layers" size={11} /> {styleName}
        </span>
      )}
    </div>
  );
}

export function WorldsHome({
  worlds,
  onOpen,
  onNew,
  onDelete,
}: {
  worlds: World[];
  onOpen: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}) {
  const [menuId, setMenuId] = useState<string | null>(null);
  const sorted = [...worlds].sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));

  return (
    <div className="home">
      <div className="home-inner">
        <header className="home-head">
          <div className="brand-lock big">
            <span style={{ color: "var(--ink)" }}>
              <BookMark size={34} />
            </span>
            <span className="wm">softbound</span>
            <span className="tag">studio</span>
          </div>
          <p className="home-sub">your worlds. quiet places, each one still until small hands arrive.</p>
        </header>

        <div className="home-row">
          <h2 className="home-h">
            your worlds<span className="home-count">{worlds.length}</span>
          </h2>
        </div>

        <div className="worlds-grid">
          <button type="button" className="newcard" onClick={onNew}>
            <span className="newcard-plus">
              <Icon name="feather" size={26} />
            </span>
            <div className="newcard-t">begin a new world</div>
            <div className="newcard-l">seed an idea — the co-author writes the rest</div>
          </button>

          {sorted.map((w) => {
            const v = (w.versions || [])[(w.versions || []).length - 1];
            const title = v ? v.title : "untitled world";
            const logline = v ? v.logline : "a world still finding its shape.";
            return (
              <div className="worldcard" key={w.id} onClick={() => onOpen(w.id)} role="button" tabIndex={0}>
                <WorldCover world={w} />
                <div className="worldcard-body">
                  <div className="worldcard-top">
                    <h3 className="worldcard-t">{title}</h3>
                    <button
                      type="button"
                      className="wc-menu"
                      onClick={(e) => {
                        e.stopPropagation();
                        setMenuId(menuId === w.id ? null : w.id);
                      }}
                      aria-label="more"
                    >
                      <Icon name="settings" size={16} />
                    </button>
                  </div>
                  <p className="worldcard-l">{logline}</p>
                  <div className="worldcard-foot">
                    <StageDots world={w} />
                    <span className="worldcard-meta">
                      {(w.versions || []).length > 0
                        ? `v${v ? v.n : 1} · ${(w.characters || []).length} in the cast`
                        : "just seeded"}
                    </span>
                  </div>
                </div>
                {menuId === w.id && (
                  <>
                    <div className="pop-scrim" onClick={(e) => { e.stopPropagation(); setMenuId(null); }} />
                    <div className="wc-pop" onClick={(e) => e.stopPropagation()}>
                      <button type="button" onClick={() => { onOpen(w.id); setMenuId(null); }}>
                        <Icon name="pen" size={15} /> open & continue
                      </button>
                      <button
                        type="button"
                        className="danger"
                        onClick={() => {
                          onDelete(w.id);
                          setMenuId(null);
                        }}
                      >
                        <Icon name="trash" size={15} /> delete world
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
