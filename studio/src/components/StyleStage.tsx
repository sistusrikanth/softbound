import { useState } from "react";
import type { BibleVersion, StyleLibrary } from "@/lib/types";
import { STYLE_DIRECTIONS } from "@/lib/engine";
import { BookMark, Icon } from "./icons";
import { AskBar } from "./shared";
import { ImageSlot } from "./ImageSlot";

function CopyBtn({ text, label = "copy" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false);
  const copy = () => {
    try {
      navigator.clipboard.writeText(text);
    } catch {
      /* ignore */
    }
    setDone(true);
    setTimeout(() => setDone(false), 1400);
  };
  return (
    <button type="button" className={"copybtn" + (done ? " done" : "")} onClick={copy}>
      <Icon name={done ? "check" : "note"} size={13} /> {done ? "copied" : label}
    </button>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="sr-field">
      <div className="sr-field-label">{label}</div>
      <div className="sr-field-value">{value}</div>
    </div>
  );
}

export function StyleStage({
  world,
  worldId,
  style,
  busy,
  onGenerate,
  onRefine,
  onAdvance,
  isMobile,
}: {
  world: BibleVersion | null;
  worldId: string;
  style: StyleLibrary | null;
  busy: boolean;
  onGenerate: (dir: (typeof STYLE_DIRECTIONS)[0], extra: string) => void;
  onRefine: (ask: string) => void;
  onAdvance: () => void;
  isMobile: boolean;
}) {
  const [picked, setPicked] = useState(style ? style.directionId : null);
  const [extra, setExtra] = useState(style ? style.extra : "");
  const [ask, setAsk] = useState("");

  const dir = STYLE_DIRECTIONS.find((d) => d.id === picked) || null;
  const generate = () => {
    if (dir) onGenerate(dir, extra);
  };
  const refine = () => {
    if (ask.trim()) {
      onRefine(ask);
      setAsk("");
    }
  };

  const worldKey = worldId;

  return (
    <div className="screen-scroll">
      <div className="screen-pad style-pad">
        <div className="screen-head">
          <div>
            <div className="screen-eyebrow">
              <Icon name="layers" size={14} /> the look of {world ? world.title.toLowerCase() : "this world"}
            </div>
            <h1 className="screen-h">give the world a style</h1>
            <p className="screen-sub">
              choose a direction, add a few words and reference frames. the co-author writes a prompt library you can hand to any image generator.
            </p>
          </div>
          {style && (
            <button type="button" className="btn primary" onClick={onAdvance}>
              on to the stories <Icon name="arrowRight" size={16} />
            </button>
          )}
        </div>

        <div className={"style-cols" + (style ? " has-result" : "")}>
          <div className="style-input">
            <div className="ce-section-label">
              <Icon name="spark" size={13} /> a direction
            </div>
            <div className="dir-grid">
              {STYLE_DIRECTIONS.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  className={"dircard" + (picked === d.id ? " on" : "")}
                  onClick={() => setPicked(d.id)}
                  style={{ "--dt": `var(--${d.tint})` } as React.CSSProperties}
                >
                  <div className="dircard-thumb">
                    {d.thumb ? (
                      <img src={d.thumb} alt="" />
                    ) : (
                      <div className="dircard-swatch" style={{ background: `var(--${d.tint})` }}>
                        <BookMark size={22} />
                      </div>
                    )}
                    {picked === d.id && (
                      <span className="dircard-check">
                        <Icon name="check" size={14} />
                      </span>
                    )}
                  </div>
                  <div className="dircard-name">{d.name}</div>
                  <div className="dircard-blurb">{d.blurb}</div>
                </button>
              ))}
            </div>

            <div className="ce-section-label" style={{ marginTop: 24 }}>
              describe the look, in your words
            </div>
            <textarea
              className="style-ta"
              rows={3}
              value={extra}
              placeholder="soft morning haze, everything a little rounded, nothing sharp…"
              onChange={(e) => setExtra(e.target.value)}
            />

            <div className="ce-section-label" style={{ marginTop: 22 }}>
              reference frames <span className="lbl-opt">optional — drop your own</span>
            </div>
            <div className="ref-slots">
              <ImageSlot id={`styleref-${worldKey}-1`} placeholder="drop a reference" />
              <ImageSlot id={`styleref-${worldKey}-2`} placeholder="drop a reference" />
              {!isMobile && <ImageSlot id={`styleref-${worldKey}-3`} placeholder="drop a reference" />}
            </div>

            <button type="button" className="btn accent style-go" disabled={!dir || busy} onClick={generate}>
              <Icon name="spark" size={16} /> {busy ? "writing the style…" : style ? "regenerate the style" : "write the style"}
            </button>
          </div>

          {style ? (
            <div className="style-result" style={{ "--st": `var(--${style.tint})` } as React.CSSProperties}>
              <div className="sr-head">
                <div>
                  <div className="sr-eyebrow">
                    <Icon name="check" size={13} /> style v{style.n} · prompt library
                  </div>
                  <div className="sr-name">{style.name}</div>
                </div>
              </div>

              <div className="sr-master">
                <div className="sr-master-head">
                  <span>master prompt</span>
                  <CopyBtn text={style.master} />
                </div>
                <div className="sr-master-text">{style.master}</div>
              </div>

              <div className="sr-grid">
                <Field label="medium" value={style.medium} />
                <Field label="materials" value={style.materials} />
                <Field label="lighting" value={style.lighting} />
                <Field label="camera" value={style.camera} />
                <Field label="texture" value={style.texture} />
                <Field label="mood" value={style.mood} />
              </div>

              <div className="sr-field">
                <div className="sr-field-label">palette</div>
                <div className="sr-palette">
                  {style.palette.map((p, i) => (
                    <span className="pillmini" key={i}>
                      {p}
                    </span>
                  ))}
                </div>
              </div>
              <div className="sr-field">
                <div className="sr-field-label">avoid</div>
                <div className="sr-negative">{style.negative}</div>
              </div>

              <div className="sr-refine">
                <div className="ce-section-label" style={{ marginBottom: 9 }}>
                  <Icon name="spark" size={13} /> refine the style
                </div>
                <AskBar
                  value={ask}
                  onChange={setAsk}
                  onSend={refine}
                  disabled={busy}
                  placeholder='"warmer light", "rougher paper edges", "less blue"…'
                />
              </div>

              <div className="sr-results">
                <div className="ce-section-label">
                  generated frames <span className="lbl-opt">drop results from your image generator</span>
                </div>
                <div className="result-slots">
                  <ImageSlot id={`styleout-${worldKey}-1`} placeholder="paste a generated frame" />
                  <ImageSlot id={`styleout-${worldKey}-2`} placeholder="paste a generated frame" />
                </div>
              </div>
            </div>
          ) : (
            <div className="style-empty">
              <div className="breathe">
                <Icon name="layers" size={48} />
              </div>
              <div className="style-empty-t">pick a direction, then write the style</div>
              <div className="style-empty-l">
                the co-author turns it into prompts you can paste into any image generator — or wire straight to an image API later.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
