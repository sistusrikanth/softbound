import type { LayoutMode, Phase, Step } from "@/lib/types";
import { SEED_PRESETS } from "@/lib/engine";
import { BookMark, Icon } from "./icons";

export function Topbar({
  onHome,
  step,
  setStep,
  worldTitle,
  hasBible,
  hasStyle,
  hasStories,
  layout,
  setLayout,
  phase,
  isMobile,
}: {
  onHome: () => void;
  step: Step;
  setStep: (s: Step) => void;
  worldTitle: string;
  hasBible: boolean;
  hasStyle: boolean;
  hasStories: boolean;
  layout: LayoutMode;
  setLayout: (v: LayoutMode) => void;
  phase: Phase;
  isMobile: boolean;
}) {
  const steps = [
    { id: "bible" as Step, label: "bible", icon: "feather", on: true },
    { id: "style" as Step, label: "style", icon: "layers", on: hasBible },
    { id: "stories" as Step, label: "stories", icon: "book", on: hasBible },
    { id: "flow" as Step, label: "flow", icon: "flow", on: hasStories },
  ];
  const doneMap: Record<Step, boolean> = { bible: hasBible, style: hasStyle, stories: hasStories, flow: false };

  return (
    <div className="topbar">
      <button type="button" className="worlds-back" onClick={onHome}>
        <Icon name="back" size={17} /> <span className="wb-label">worlds</span>
      </button>
      <div className="topbar-divider" />
      <div className="topbar-world">
        <BookMark size={20} />
        <span className="tw-title">{worldTitle}</span>
      </div>
      <div className="spacer" />
      <div className="stepper">
        {steps.map((s, i) => (
          <span key={s.id} style={{ display: "contents" }}>
            {i > 0 && (
              <span className="step-link">
                <Icon name="chevronRight" size={15} />
              </span>
            )}
            <button
              type="button"
              className={"step" + (step === s.id ? " active" : doneMap[s.id] ? " done" : s.on ? "" : " locked")}
              disabled={!s.on}
              onClick={() => s.on && setStep(s.id)}
            >
              <span className="si">
                {step === s.id ? (
                  <Icon name={s.icon} size={13} />
                ) : doneMap[s.id] ? (
                  <Icon name="check" size={13} />
                ) : (
                  <Icon name={s.icon} size={13} />
                )}
              </span>
              <span className="sl">{s.label}</span>
            </button>
          </span>
        ))}
      </div>
      <div className="spacer" />
      {!isMobile && step === "bible" && phase === "ready" && (
        <div className="seg">
          <button type="button" className={layout === "manuscript" ? "on" : ""} onClick={() => setLayout("manuscript")}>
            <Icon name="note" size={15} /> manuscript
          </button>
          <button type="button" className={layout === "studio" ? "on" : ""} onClick={() => setLayout("studio")}>
            <Icon name="layers" size={15} /> studio
          </button>
        </div>
      )}
      <button type="button" className="icon-btn topbar-settings" title="settings">
        <Icon name="settings" size={19} />
      </button>
    </div>
  );
}

export function SeedScreen({
  seedText,
  setSeedText,
  onBegin,
}: {
  seedText: string;
  setSeedText: (v: string) => void;
  onBegin: (text: string, presetId: string | null) => void;
}) {
  return (
    <div className="seed-screen">
      <div className="seed-inner">
        <div className="seed-eyebrow">
          <Icon name="spark" size={14} /> a new world
        </div>
        <h1 className="seed-h">what is this world?</h1>
        <p className="seed-sub">
          say it the way you'd whisper it to a child. the co-author writes the world and its first characters in the softbound voice — and you can change anything.
        </p>
        <div className="seed-card">
          <textarea
            className="seed-ta"
            rows={3}
            value={seedText}
            autoFocus
            placeholder="a sleepy lighthouse on a foggy coast, where a small keeper lights a lamp for lost boats…"
            onChange={(e) => setSeedText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onBegin(seedText, null);
            }}
          />
          <div className="seed-row">
            <span className="seed-hint">the co-author writes in the softbound voice — hushed, slow, kind.</span>
            <button type="button" className="btn accent" disabled={!seedText.trim()} onClick={() => onBegin(seedText, null)}>
              <Icon name="feather" size={16} /> begin the bible
            </button>
          </div>
        </div>
        <div className="chips">
          <span className="seed-hint" style={{ alignSelf: "center" }}>
            or start from a seed —
          </span>
          {SEED_PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              className="chip"
              onClick={() => {
                setSeedText(p.seed);
                onBegin(p.seed, p.id);
              }}
            >
              <span className="ci">
                <Icon name={p.icon} size={14} />
              </span>{" "}
              {p.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export function Thinking() {
  return (
    <div className="thinking">
      <div className="thinking-inner">
        <div className="breathe">
          <BookMark size={64} />
        </div>
        <div className="thinking-label">the co-author is writing your world and its cast, slowly…</div>
        <div className="shimmer-lines">
          <div className="shimmer" style={{ width: "92%" }} />
          <div className="shimmer" style={{ width: "100%" }} />
          <div className="shimmer" style={{ width: "78%" }} />
        </div>
      </div>
    </div>
  );
}

export function FlowScreen({ stories }: { stories: import("@/lib/types").Story[] }) {
  const nodes = [
    { key: "day_idle", t: "morning", start: true, x: 60, y: 60, g: "tap the sky" },
    { key: "rooster", t: "the crow", x: 320, y: 40, g: "tap the rooster" },
    { key: "night_idle", t: "evening", x: 320, y: 250, g: "tap the sky" },
    { key: "fireflies", t: "the glow", x: 600, y: 230, g: "tap to wake" },
  ];

  return (
    <div className="screen-scroll">
      <div className="screen-pad">
        <div className="screen-head">
          <div>
            <div className="screen-eyebrow">
              <Icon name="flow" size={14} /> {stories[0] ? stories[0].title.toLowerCase() : "a story"}
            </div>
            <h1 className="screen-h">the flow</h1>
            <p className="screen-sub">
              each page is a still scene; each line is a gesture a small hand can make. the co-author drafts the wiring — you keep what feels right.
            </p>
          </div>
          <button type="button" className="btn secondary">
            <Icon name="play" size={16} /> preview
          </button>
        </div>
        <div className="flow-canvas">
          <div className="dots" />
          <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
            <path d="M218 120 C 280 120, 280 90, 320 90" fill="none" stroke="var(--accent)" strokeWidth="1.6" strokeDasharray="1 6" strokeLinecap="round" />
            <path d="M140 175 C 140 250, 250 290, 320 290" fill="none" stroke="var(--accent)" strokeWidth="1.6" strokeDasharray="1 6" strokeLinecap="round" />
            <path d="M478 290 C 540 290, 540 280, 600 280" fill="none" stroke="var(--accent)" strokeWidth="1.6" strokeDasharray="1 6" strokeLinecap="round" />
          </svg>
          {nodes.map((n) => (
            <div className={"fnode" + (n.start ? " start" : "")} style={{ left: n.x, top: n.y }} key={n.key}>
              <div className="fk">{n.start ? "start · " : ""}page</div>
              <div className="ft">{n.t}</div>
              <div className="fthumb" />
              <div className="fchip">
                <Icon name="hand" size={12} /> {n.g}
              </div>
            </div>
          ))}
        </div>
        <div className="stub-note">
          <Icon name="flow" size={14} /> you design the touches · the co-author wires the scenes — the existing workflow canvas, in softbound clothes.
        </div>
      </div>
    </div>
  );
}
