import { useState } from "react";
import type { Character, WorldTint } from "@/lib/types";
import { Icon } from "./icons";
import { AskBar } from "./shared";

const TINT_VAR: Record<WorldTint, string> = {
  clay: "var(--clay)",
  sage: "var(--sage)",
  sky: "var(--sky)",
  honey: "var(--honey)",
  rose: "var(--rose)",
};

const TINT_DEEP: Record<WorldTint, string> = {
  clay: "var(--clay-deep)",
  sage: "#5A6B52",
  sky: "#6E8794",
  honey: "#B4904A",
  rose: "#B97A6E",
};

function monogram(name: string) {
  const cleaned = (name || "?").replace(/^(the|a|an)\s+/i, "").trim();
  return (cleaned[0] || "?").toUpperCase();
}

export function CharToken({ char, size = 38 }: { char: Character; size?: number }) {
  return (
    <span
      className="ctoken"
      style={{
        width: size,
        height: size,
        background: TINT_VAR[char.tint] || "var(--clay)",
        fontSize: size * 0.42,
      }}
      title={char.name}
    >
      {monogram(char.name)}
    </span>
  );
}

export function CastControl({
  characters,
  onOpen,
  active,
  dirty,
}: {
  characters: Character[];
  onOpen: () => void;
  active: boolean;
  dirty: boolean;
}) {
  const shown = characters.slice(0, 4);
  return (
    <button type="button" className={"cast-control" + (active ? " on" : "")} onClick={onOpen}>
      <div className="cast-stack">
        {shown.map((c, i) => (
          <span
            key={c.id}
            className="ctoken sm"
            style={{
              background: TINT_VAR[c.tint] || "var(--clay)",
              marginLeft: i === 0 ? 0 : -10,
              zIndex: shown.length - i,
            }}
          >
            {monogram(c.name)}
          </span>
        ))}
        {characters.length === 0 && (
          <span className="ctoken sm empty">
            <Icon name="hand" size={14} />
          </span>
        )}
      </div>
      <span className="cast-label">
        cast<span className="cast-n">{characters.length}</span>
      </span>
      {dirty && <span className="cast-dot" title="the cast has changed" />}
    </button>
  );
}

export function CastPopover({
  characters,
  onClose,
  onEdit,
  onAdd,
  onReweave,
  dirty,
  busy,
}: {
  characters: Character[];
  onClose: () => void;
  onEdit: (id: string) => void;
  onAdd: () => void;
  onReweave: () => void;
  dirty: boolean;
  busy: boolean;
}) {
  return (
    <>
      <div className="pop-scrim" onClick={onClose} />
      <div className="cast-pop">
        <div className="cast-pop-head">
          <div>
            <div className="cast-pop-title">the cast</div>
            <div className="cast-pop-sub">the people and creatures of this world. each one evolves on its own.</div>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="close">
            <Icon name="close" size={18} />
          </button>
        </div>

        {dirty && characters.length > 0 && (
          <button type="button" className="reweave" onClick={onReweave} disabled={busy}>
            <span className="rw-i">
              <Icon name="spark" size={16} />
            </span>
            <span className="rw-t">
              <strong>the cast has grown.</strong>
              <small>{busy ? "reweaving the bible…" : "reweave the world bible so it reflects who they've become"}</small>
            </span>
            {!busy && <Icon name="arrowRight" size={16} />}
          </button>
        )}

        <div className="cast-grid">
          {characters.map((c) => (
            <button
              key={c.id}
              type="button"
              className="ccard"
              onClick={() => onEdit(c.id)}
              style={{ "--tint": TINT_VAR[c.tint], "--tintd": TINT_DEEP[c.tint] } as React.CSSProperties}
            >
              <div className="ccard-top">
                <CharToken char={c} size={42} />
                <div className="ccard-id">
                  <div className="ccard-name">{c.name}</div>
                  <div className="ccard-role">{c.role}</div>
                </div>
                {c.n > 1 && <span className="ccard-v">v{c.n}</span>}
              </div>
              <div className="ccard-bio">{c.bio}</div>
              <div className="ccard-themes">
                {c.themes.slice(0, 4).map((t) => (
                  <span className="theme" key={t}>
                    {t}
                  </span>
                ))}
              </div>
            </button>
          ))}
          <button type="button" className="ccard add" onClick={onAdd}>
            <span className="add-plus">
              <Icon name="plus" size={22} />
            </span>
            <div className="ccard-name">add a character</div>
            <div className="ccard-role">seed one, the co-author fills it in</div>
          </button>
        </div>
      </div>
    </>
  );
}

export function CharacterEditor({
  char,
  onClose,
  onField,
  onRefine,
  onAddTheme,
  onRemoveTheme,
  onRemove,
  busy,
  isNew,
}: {
  char: Character;
  onClose: () => void;
  onField: (f: keyof Character, v: string | string[]) => void;
  onRefine: (ask: string) => void;
  onAddTheme: (theme: string) => void;
  onRemoveTheme: (theme: string) => void;
  onRemove: () => void;
  busy: boolean;
  isNew: boolean;
}) {
  const [ask, setAsk] = useState("");
  const [theme, setTheme] = useState("");

  const send = () => {
    if (ask.trim()) {
      onRefine(ask);
      setAsk("");
    }
  };
  const addT = () => {
    const v = theme.trim().toLowerCase();
    if (v) {
      onAddTheme(v);
      setTheme("");
    }
  };

  return (
    <>
      <div className="editor-scrim" onClick={onClose} />
      <div className="char-editor" style={{ "--tint": TINT_VAR[char.tint], "--tintd": TINT_DEEP[char.tint] } as React.CSSProperties}>
        <button type="button" className="icon-btn ce-close" onClick={onClose} aria-label="close">
          <Icon name="close" size={18} />
        </button>

        <div className="ce-head">
          <CharToken char={char} size={64} />
          <div className="ce-id">
            <input className="ce-name" value={char.name} placeholder="name" onChange={(e) => onField("name", e.target.value)} />
            <input
              className="ce-role"
              value={char.role}
              placeholder='a short epithet — "warden of small mornings"'
              onChange={(e) => onField("role", e.target.value)}
            />
          </div>
          <div className="ce-vtag">{isNew ? "new" : "v" + char.n}</div>
        </div>

        <div className="ce-section-label">who they are</div>
        <textarea
          className="ce-bio"
          value={char.bio}
          placeholder="seed a sentence, or ask the co-author below to write them…"
          onChange={(e) => onField("bio", e.target.value)}
          rows={4}
        />

        <div className="ce-section-label">themes they carry</div>
        <div className="ce-themes">
          {char.themes.map((t) => (
            <span className="theme removable" key={t} onClick={() => onRemoveTheme(t)}>
              {t}
              <Icon name="close" size={11} />
            </span>
          ))}
          <span className="theme-add">
            <input
              value={theme}
              placeholder="add theme"
              onChange={(e) => setTheme(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") addT();
              }}
            />
          </span>
        </div>

        <div className="ce-coauthor">
          <div className="ce-section-label" style={{ marginBottom: 9 }}>
            <Icon name="spark" size={13} /> {isNew ? "seed this character" : "refine with the co-author"}
          </div>
          <AskBar
            value={ask}
            onChange={setAsk}
            onSend={send}
            disabled={busy}
            placeholder={
              isNew
                ? 'who is this? — "a shy mole who loves the rain"…'
                : '"make her braver", "give him a quiet habit"…'
            }
          />
        </div>

        <div className="ce-foot">
          <button type="button" className="btn ghost sm danger" onClick={onRemove}>
            <Icon name="trash" size={15} /> remove
          </button>
          <button type="button" className="btn secondary sm" onClick={onClose}>
            done
          </button>
        </div>
      </div>
    </>
  );
}
