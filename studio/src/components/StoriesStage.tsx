import { useState } from "react";
import type { BibleVersion, Story } from "@/lib/types";
import { Icon } from "./icons";
import { AskBar } from "./shared";

function StoryCard({
  story,
  onOpen,
  onSave,
  onDismiss,
}: {
  story: Story;
  onOpen: (id: string) => void;
  onSave: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  return (
    <div className={"story-card" + (story.proposed ? " proposed" : " saved")} onClick={() => onOpen(story.id)} role="button" tabIndex={0}>
      {story.proposed ? (
        <span className="sc-prop">
          <Icon name="sparkSmall" size={11} /> proposed
        </span>
      ) : (
        <span className="sc-prop saved">
          <Icon name="check" size={11} /> saved{story.n > 1 ? " · v" + story.n : ""}
        </span>
      )}
      <span className="pillmini" style={{ alignSelf: "flex-start" }}>
        <Icon name="book" size={12} /> story
      </span>
      <div className="sc-t">{story.title}</div>
      <div className="sc-l">{story.logline}</div>
      <div className="sc-meta">
        <span className="pillmini">
          <Icon name="layers" size={12} /> {story.scenes} scenes
        </span>
        {(story.gestures || []).map((g) => (
          <span className="pillmini" key={g}>
            <Icon name="hand" size={12} /> {g}
          </span>
        ))}
      </div>
      <div className="sc-actions" onClick={(e) => e.stopPropagation()}>
        {story.proposed ? (
          <>
            <button type="button" className="btn ghost sm" onClick={() => onDismiss(story.id)}>
              not this one
            </button>
            <button type="button" className="btn accent sm" onClick={() => onSave(story.id)}>
              <Icon name="check" size={14} /> keep it
            </button>
          </>
        ) : (
          <button type="button" className="btn secondary sm" onClick={() => onOpen(story.id)}>
            <Icon name="pen" size={14} /> open & edit
          </button>
        )}
      </div>
    </div>
  );
}

export function StoriesStage({
  world,
  stories,
  busy,
  view,
  setView,
  onOpen,
  onSave,
  onDismiss,
  onProposeMore,
  onAdvance,
  bibleVersionLabel,
}: {
  world: BibleVersion | null;
  stories: Story[];
  busy: boolean;
  view: "saved" | "proposed";
  setView: (v: "saved" | "proposed") => void;
  onOpen: (id: string) => void;
  onSave: (id: string) => void;
  onDismiss: (id: string) => void;
  onProposeMore: () => void;
  onAdvance: () => void;
  bibleVersionLabel: string;
}) {
  const saved = stories.filter((s) => !s.proposed);
  const proposed = stories.filter((s) => s.proposed);
  const list = view === "saved" ? saved : proposed;

  return (
    <div className="screen-scroll">
      <div className="screen-pad">
        <div className="screen-head">
          <div>
            <div className="screen-eyebrow">
              <Icon name="book" size={14} /> the stories inside {world ? world.title.toLowerCase() : "this world"}
            </div>
            <h1 className="screen-h">stories</h1>
            <p className="screen-sub">
              keep the ones that feel right; ask for more whenever you like. new proposals are shaped by your bible and the stories you've kept.
            </p>
          </div>
          {saved.length > 0 && (
            <button type="button" className="btn primary" onClick={onAdvance}>
              build the flow <Icon name="arrowRight" size={16} />
            </button>
          )}
        </div>

        <div className="stories-bar">
          <div className="seg shelf-seg">
            <button type="button" className={view === "saved" ? "on" : ""} onClick={() => setView("saved")}>
              <Icon name="check" size={15} /> saved <span className="seg-n">{saved.length}</span>
            </button>
            <button type="button" className={view === "proposed" ? "on" : ""} onClick={() => setView("proposed")}>
              <Icon name="spark" size={15} /> proposed <span className="seg-n">{proposed.length}</span>
            </button>
          </div>
          <div className="spacer" />
          {view === "proposed" && (
            <span className="bible-cond">
              <Icon name="feather" size={13} /> conditioned on {bibleVersionLabel}
              {saved.length ? ` + ${saved.length} saved` : ""}
            </span>
          )}
          <button
            type="button"
            className="btn secondary sm"
            disabled={busy}
            onClick={() => {
              setView("proposed");
              onProposeMore();
            }}
          >
            <Icon name="spark" size={15} /> {busy ? "thinking…" : "propose more"}
          </button>
        </div>

        {list.length > 0 ? (
          <div className="story-grid">
            {list.map((s) => (
              <StoryCard key={s.id} story={s} onOpen={onOpen} onSave={onSave} onDismiss={onDismiss} />
            ))}
            {view === "saved" && (
              <button
                type="button"
                className="story-card add"
                onClick={() => {
                  setView("proposed");
                  onProposeMore();
                }}
              >
                <Icon name="spark" size={22} />
                <div className="sc-t" style={{ marginTop: 4 }}>
                  ask for more stories
                </div>
                <div className="sc-l" style={{ textAlign: "center" }}>
                  shaped by your bible & saved stories
                </div>
              </button>
            )}
          </div>
        ) : (
          <div className="stories-empty">
            <div className="breathe">
              <Icon name={view === "saved" ? "book" : "spark"} size={44} />
            </div>
            <div className="style-empty-t">{view === "saved" ? "no stories kept yet" : "no proposals right now"}</div>
            <div className="style-empty-l">
              {view === "saved"
                ? "keep a proposed story and it lands here, ready to edit."
                : "ask the co-author to propose a few."}
            </div>
            {view === "proposed" && (
              <button type="button" className="btn accent" style={{ marginTop: 18 }} disabled={busy} onClick={onProposeMore}>
                <Icon name="spark" size={16} /> propose stories
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function StoryEditor({
  story,
  onClose,
  onField,
  onBeat,
  onAddBeat,
  onRemoveBeat,
  onRefine,
  onSave,
  busy,
}: {
  story: Story;
  onClose: () => void;
  onField: (f: "title" | "logline", v: string) => void;
  onBeat: (bid: string, v: string) => void;
  onAddBeat: () => void;
  onRemoveBeat: (bid: string) => void;
  onRefine: (ask: string) => void;
  onSave: (id: string) => void;
  busy: boolean;
}) {
  const [ask, setAsk] = useState("");
  const send = () => {
    if (ask.trim()) {
      onRefine(ask);
      setAsk("");
    }
  };

  return (
    <>
      <div className="editor-scrim" onClick={onClose} />
      <div className="char-editor story-editor">
        <button type="button" className="icon-btn ce-close" onClick={onClose} aria-label="close">
          <Icon name="close" size={18} />
        </button>
        <div className="se-head">
          <span className="se-badge">{story.proposed ? "proposed" : "saved" + (story.n > 1 ? " · v" + story.n : "")}</span>
          <input className="ce-name" value={story.title} placeholder="story title" onChange={(e) => onField("title", e.target.value)} />
          <input
            className="ce-role"
            value={story.logline}
            placeholder="one quiet sentence about it"
            onChange={(e) => onField("logline", e.target.value)}
          />
        </div>

        <div className="ce-section-label">the beats</div>
        <div className="se-beats">
          {(story.beats || []).map((b, i) => (
            <div className="se-beat" key={b.id}>
              <span className="se-beat-n">{i + 1}</span>
              <input value={b.text} placeholder="what happens in this scene…" onChange={(e) => onBeat(b.id, e.target.value)} />
              <button type="button" className="se-beat-x" onClick={() => onRemoveBeat(b.id)} aria-label="remove beat">
                <Icon name="close" size={14} />
              </button>
            </div>
          ))}
          <button type="button" className="se-addbeat" onClick={onAddBeat}>
            <Icon name="plus" size={15} /> add a beat
          </button>
        </div>

        <div className="ce-coauthor">
          <div className="ce-section-label" style={{ marginBottom: 9 }}>
            <Icon name="spark" size={13} /> refine with the co-author
          </div>
          <AskBar
            value={ask}
            onChange={setAsk}
            onSend={send}
            disabled={busy}
            placeholder='"make it about being brave", "add a sleepy ending"…'
          />
        </div>

        <div className="ce-foot">
          <span className="se-scenes">{(story.beats || []).length} beats</span>
          {story.proposed ? (
            <button
              type="button"
              className="btn accent sm"
              onClick={() => {
                onSave(story.id);
                onClose();
              }}
            >
              <Icon name="check" size={15} /> keep this story
            </button>
          ) : (
            <button type="button" className="btn secondary sm" onClick={onClose}>
              done
            </button>
          )}
        </div>
      </div>
    </>
  );
}
