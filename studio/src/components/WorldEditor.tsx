import { useCallback, useEffect, useState } from "react";
import type { ComposingState, LayoutMode, Note, Phase, SelectionState, Step, TimelineEntry, Tweaks, World } from "@/lib/types";
import {
  aiFleshCharacter,
  aiGenerate,
  aiProposeStories,
  aiRegenWithCast,
  aiRevise,
  aiReviseCharacter,
  aiReviseStory,
  aiSeedCharacters,
  aiStyleLibrary,
  STYLE_DIRECTIONS,
} from "@/lib/engine";
import {
  castSummary,
  delay,
  makeVersion,
  newId,
  TINTS,
  withParaIds,
} from "@/lib/storage";
import { CastPopover, CharacterEditor } from "./characters";
import { ManuscriptView } from "./ManuscriptView";
import { StudioView } from "./StudioView";
import { StoriesStage, StoryEditor } from "./StoriesStage";
import { StyleStage } from "./StyleStage";
import { FlowScreen, SeedScreen, Thinking, Topbar } from "./screens";
import { Icon } from "./icons";
import {
  ACCENTS,
  TweakButton,
  TweakColor,
  TweakRadio,
  TweakSection,
  TweaksPanel,
  TweakToggle,
} from "./TweaksPanel";

export function WorldEditor({
  world,
  onPersist,
  onHome,
  isMobile,
  t,
  setTweak,
}: {
  world: World;
  onPersist: (id: string, obj: Partial<World>) => void;
  onHome: () => void;
  isMobile: boolean;
  t: Tweaks;
  setTweak: <K extends keyof Tweaks>(key: K, val: Tweaks[K]) => void;
}) {
  const [step, setStep] = useState<Step>(world.step || "bible");
  const [phase, setPhase] = useState<Phase>(world.phase || "seed");
  const [seedText, setSeedText] = useState("");
  const [versions, setVersions] = useState(world.versions || []);
  const [current, setCurrent] = useState(world.current ?? 0);
  const [notesByVersion, setNotes] = useState(world.notesByVersion || {});
  const [timeline, setTimeline] = useState<TimelineEntry[]>(world.timeline || []);
  const [stories, setStories] = useState(world.stories || []);
  const [characters, setCharacters] = useState(world.characters || []);
  const [castDirty, setCastDirty] = useState(world.castDirty || false);
  const [style, setStyle] = useState(world.style || null);
  const [flowStarted, setFlowStarted] = useState(world.flowStarted || false);

  const [castOpen, setCastOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newCharId, setNewCharId] = useState<string | null>(null);
  const [busyChar, setBusyChar] = useState(false);
  const [busyStyle, setBusyStyle] = useState(false);
  const [busyStory, setBusyStory] = useState(false);
  const [storyView, setStoryView] = useState<"saved" | "proposed">("proposed");
  const [editingStoryId, setEditingStoryId] = useState<string | null>(null);

  const [sel, setSel] = useState<SelectionState | null>(null);
  const [composing, setComposing] = useState<ComposingState | null>(null);
  const [draft, setDraft] = useState("");
  const [activeNoteId, setActiveNoteId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    onPersist(world.id, {
      step,
      phase,
      versions,
      current,
      notesByVersion,
      timeline,
      stories,
      characters,
      castDirty,
      style,
      flowStarted,
      tint: style ? style.tint : world.tint,
    });
  }, [step, phase, versions, current, notesByVersion, timeline, stories, characters, castDirty, style, flowStarted]);

  const view = versions[current];
  const latestBible = versions[versions.length - 1];
  const isHistorical = current !== versions.length - 1;
  const notes = (view && notesByVersion[view.id]) || [];
  const maxN = versions.reduce((m, v) => Math.max(m, v.n), 0);
  const editingChar = characters.find((c) => c.id === editingId) || null;
  const editingStory = stories.find((s) => s.id === editingStoryId) || null;

  const beginGenerate = useCallback(async (text: string, presetId: string | null) => {
    if (!text.trim()) return;
    setPhase("thinking");
    setBusy(true);
    setTimeline([{ kind: "seed", text }]);
    const [bible, cast] = await Promise.all([aiGenerate(text, presetId), aiSeedCharacters(text, presetId), delay(1700)]);
    const v1 = makeVersion(withParaIds(bible), { n: 1, changeSummary: "first draft", basedOn: null });
    setVersions([v1]);
    setCurrent(0);
    setNotes({ [v1.id]: [] });
    setCharacters(cast);
    setCastDirty(false);
    setTimeline((tl) => [
      ...tl,
      { kind: "ai-draft", vN: 1, text: `drafted a first bible and a cast of ${cast.length} — ${castSummary(cast)}.` },
    ]);
    setPhase("ready");
    setBusy(false);
  }, []);

  const applyRevision = useCallback(
    async (note: Note, asTimeline: TimelineEntry) => {
      setBusy(true);
      const prev = versions[current];
      setTimeline((tl) => [...tl, asTimeline]);
      const result = await Promise.all([aiRevise(prev, note), delay(1500)]).then(([r]) => r);
      const newParas = result.paras.map((p, i) => {
        const prevP = prev.paras[i];
        const changed = !prevP || (prevP.text || "").trim() !== (p.text || "").trim();
        return {
          id: prevP ? prevP.id : newId("p"),
          role: prevP ? prevP.role : "body",
          heading: p.heading,
          text: p.text,
          revised: changed,
        };
      });
      if (!newParas.some((p) => p.revised)) {
        const idx = prev.paras.findIndex((p) => p.id === note.paraId);
        if (idx >= 0 && newParas[idx]) newParas[idx].revised = true;
      }
      const nv = makeVersion(
        { title: result.title, logline: result.logline, paras: newParas },
        { n: maxN + 1, changeSummary: result.summary, basedOn: prev.n },
      );
      setVersions((vs) => [...vs, nv]);
      setNotes((nb) => {
        const next = { ...nb, [nv.id]: [] };
        if (note.quote) next[prev.id] = [...(nb[prev.id] || []), { ...note, resolved: true, resolvedIn: nv.n }];
        return next;
      });
      setCurrent(versions.length);
      setTimeline((tl) => [
        ...tl,
        { kind: "ai-revise", vN: nv.n, text: note.quote ? "wove your note into the bible." : "revised the bible." },
      ]);
      setComposing(null);
      setDraft("");
      setSel(null);
      setActiveNoteId(null);
      setBusy(false);
    },
    [versions, current, maxN],
  );

  const onWeave = () => {
    if (draft.trim() && composing)
      applyRevision(
        { id: newId("n"), paraId: composing.paraId, quote: composing.quote, text: draft },
        { kind: "note", text: draft, quote: composing.quote },
      );
  };

  const onAsk = (text: string) => {
    if (text.trim() && view)
      applyRevision({ id: newId("n"), paraId: view.paras[0].id, quote: "", text }, { kind: "ask", text });
  };

  const onMouseUp = useCallback(() => {
    if (isHistorical || busy) return;
    const s = window.getSelection();
    const text = s?.toString().trim();
    if (!text || text.length < 2) {
      setSel(null);
      return;
    }
    let node: Node | null = s?.anchorNode ?? null;
    while (node && !(node.nodeType === 1 && (node as Element).hasAttribute?.("data-para"))) node = node.parentNode;
    if (!node) {
      setSel(null);
      return;
    }
    const rect = s!.getRangeAt(0).getBoundingClientRect();
    setSel({
      paraId: (node as Element).getAttribute("data-para")!,
      quote: text,
      rect: { left: rect.left + rect.width / 2, top: rect.top },
    });
  }, [isHistorical, busy]);

  const openCompose = () => {
    if (!sel) return;
    setComposing({ paraId: sel.paraId, quote: sel.quote });
    setDraft("");
    setSel(null);
    window.getSelection()?.removeAllRanges();
  };

  const onGo = (i: number) => {
    setCurrent(Math.max(0, Math.min(versions.length - 1, i)));
    setComposing(null);
    setSel(null);
    setActiveNoteId(null);
  };

  const onTitleChange = (text: string) => {
    if (!isHistorical && text.trim())
      setVersions((vs) => vs.map((v, i) => (i === current ? { ...v, title: text.trim() } : v)));
  };

  const onMarkClick = (id: string) => setActiveNoteId((a) => (a === id ? null : id));

  const editChar = (id: string) => {
    setEditingId(id);
    setCastOpen(false);
  };

  const updateChar = (id: string, patch: Partial<(typeof characters)[0]>) =>
    setCharacters((cs) => cs.map((c) => (c.id === id ? { ...c, ...patch } : c)));

  const onCharField = (f: keyof (typeof characters)[0], v: string | string[]) => {
    if (editingId) {
      updateChar(editingId, { [f]: v } as Partial<(typeof characters)[0]>);
      setCastDirty(true);
    }
  };

  const onAddTheme = (theme: string) => {
    if (editingId) {
      const c = characters.find((x) => x.id === editingId);
      if (c && !c.themes.includes(theme)) {
        updateChar(editingId, { themes: [...c.themes, theme] });
        setCastDirty(true);
      }
    }
  };

  const onRemoveTheme = (theme: string) => {
    if (editingId) {
      const c = characters.find((x) => x.id === editingId);
      if (c) {
        updateChar(editingId, { themes: c.themes.filter((x) => x !== theme) });
        setCastDirty(true);
      }
    }
  };

  const onRefineChar = useCallback(
    async (askText: string) => {
      if (!editingId) return;
      const c = characters.find((x) => x.id === editingId);
      if (!c) return;
      setBusyChar(true);
      const isNew = newCharId === editingId;
      const updated = await Promise.all([
        isNew ? aiFleshCharacter(c, askText) : aiReviseCharacter(c, askText),
        delay(1200),
      ]).then(([u]) => u);
      setCharacters((cs) => cs.map((x) => (x.id === editingId ? { ...updated, id: x.id, tint: x.tint } : x)));
      if (isNew) setNewCharId(null);
      setCastDirty(true);
      setBusyChar(false);
    },
    [editingId, characters, newCharId],
  );

  const addCharacter = () => {
    const tint = TINTS[characters.length % TINTS.length];
    const c = { id: newId("c"), n: 1, tint, name: "a new one", role: "", bio: "", themes: [] as string[] };
    setCharacters((cs) => [...cs, c]);
    setNewCharId(c.id);
    setEditingId(c.id);
    setCastOpen(false);
  };

  const removeChar = () => {
    if (!editingId) return;
    setCharacters((cs) => cs.filter((c) => c.id !== editingId));
    if (newCharId === editingId) setNewCharId(null);
    setEditingId(null);
    setCastDirty(true);
  };

  const reweave = useCallback(async () => {
    if (!latestBible || !characters.length) return;
    setBusy(true);
    setBusyChar(true);
    setTimeline((tl) => [...tl, { kind: "note", text: "reweave the bible with the updated cast." }]);
    const result = await Promise.all([aiRegenWithCast(latestBible, characters), delay(1600)]).then(([r]) => r);
    const newParas = result.paras.map((p, i) => ({
      id: latestBible.paras[i] ? latestBible.paras[i].id : newId("p"),
      role: latestBible.paras[i] ? latestBible.paras[i].role : "body",
      heading: p.heading,
      text: p.text,
      revised: !!p.revised,
    }));
    const nv = makeVersion(
      { title: result.title, logline: result.logline, paras: newParas },
      { n: maxN + 1, changeSummary: result.summary, basedOn: latestBible.n },
    );
    setVersions((vs) => [...vs, nv]);
    setNotes((nb) => ({ ...nb, [nv.id]: [] }));
    setCurrent(versions.length);
    setTimeline((tl) => [...tl, { kind: "ai-revise", vN: nv.n, text: "rewove the bible around the cast." }]);
    setCastDirty(false);
    setCastOpen(false);
    setBusy(false);
    setBusyChar(false);
  }, [latestBible, characters, maxN, versions.length]);

  const onGenerateStyle = useCallback(
    async (dir: (typeof STYLE_DIRECTIONS)[0], extra: string) => {
      setBusyStyle(true);
      const lib = await Promise.all([aiStyleLibrary(latestBible, dir, extra), delay(1500)]).then(([l]) => l);
      setStyle({ ...lib, n: style && style.directionId === dir.id ? style.n + 1 : 1 });
      setBusyStyle(false);
    },
    [latestBible, style],
  );

  const onRefineStyle = useCallback(
    async (askText: string) => {
      if (!style) return;
      setBusyStyle(true);
      const dir = STYLE_DIRECTIONS.find((d) => d.id === style.directionId) || STYLE_DIRECTIONS[0];
      const combinedExtra = (style.extra ? style.extra + ". " : "") + askText;
      const lib = await Promise.all([aiStyleLibrary(latestBible, dir, combinedExtra), delay(1400)]).then(([l]) => l);
      setStyle({ ...lib, n: style.n + 1 });
      setBusyStyle(false);
    },
    [style, latestBible],
  );

  const proposeMore = useCallback(async () => {
    if (!latestBible) return;
    setBusyStory(true);
    const existing = stories.filter((s) => !s.proposed);
    const fresh = await Promise.all([aiProposeStories(latestBible, existing, 3), delay(1500)]).then(([f]) => f);
    setStories((ss) => [...ss, ...fresh]);
    setBusyStory(false);
  }, [latestBible, stories]);

  const saveStory = (id: string) => setStories((ss) => ss.map((s) => (s.id === id ? { ...s, proposed: false } : s)));
  const dismissStory = (id: string) => {
    setStories((ss) => ss.filter((s) => s.id !== id));
    if (editingStoryId === id) setEditingStoryId(null);
  };

  const onStoryField = (f: "title" | "logline", v: string) => {
    if (editingStoryId) setStories((ss) => ss.map((s) => (s.id === editingStoryId ? { ...s, [f]: v } : s)));
  };

  const onStoryBeat = (bid: string, v: string) => {
    if (editingStoryId)
      setStories((ss) =>
        ss.map((s) =>
          s.id === editingStoryId ? { ...s, beats: s.beats.map((b) => (b.id === bid ? { ...b, text: v } : b)) } : s,
        ),
      );
  };

  const onAddBeat = () => {
    if (editingStoryId)
      setStories((ss) =>
        ss.map((s) =>
          s.id === editingStoryId
            ? { ...s, beats: [...(s.beats || []), { id: newId("b"), text: "" }], scenes: (s.beats || []).length + 1 }
            : s,
        ),
      );
  };

  const onRemoveBeat = (bid: string) => {
    if (editingStoryId)
      setStories((ss) =>
        ss.map((s) =>
          s.id === editingStoryId
            ? { ...s, beats: s.beats.filter((b) => b.id !== bid), scenes: Math.max(1, s.beats.length - 1) }
            : s,
        ),
      );
  };

  const onRefineStory = useCallback(
    async (askText: string) => {
      if (!editingStoryId) return;
      const s = stories.find((x) => x.id === editingStoryId);
      if (!s) return;
      setBusyStory(true);
      const updated = await Promise.all([aiReviseStory(s, askText), delay(1200)]).then(([u]) => u);
      setStories((ss) => ss.map((x) => (x.id === editingStoryId ? { ...updated, id: x.id, proposed: x.proposed } : x)));
      setBusyStory(false);
    },
    [editingStoryId, stories],
  );

  useEffect(() => {
    if (step === "stories" && latestBible && stories.length === 0 && !busyStory) {
      setStoryView("proposed");
      proposeMore();
    }
  }, [step]);

  const goStyle = () => setStep("style");
  const goStories = () => {
    setStep("stories");
    if (!stories.length && latestBible) {
      setStoryView("proposed");
      proposeMore();
    }
  };
  const goFlow = () => {
    setFlowStarted(true);
    setStep("flow");
  };

  const viewProps = {
    view: view!,
    versions,
    current,
    onGo,
    notes,
    activeNoteId,
    composing,
    draft,
    setDraft,
    onWeave,
    onCancel: () => setComposing(null),
    onTitleChange,
    onMouseUp,
    onMarkClick,
    onAsk,
    busy,
    timeline,
    isHistorical,
    onApprove: goStyle,
    characters,
    onOpenCast: () => setCastOpen(true),
    castOpen,
    castDirty,
    isMobile,
  };

  const effectiveLayout: LayoutMode = isMobile ? "manuscript" : t.layout;
  const savedStories = stories.filter((s) => !s.proposed);

  return (
    <div className={"app" + (t.grain ? " grain" : "")} style={{ fontSize: 16 }}>
      <Topbar
        onHome={onHome}
        step={step}
        setStep={setStep}
        worldTitle={latestBible ? latestBible.title : "new world"}
        hasBible={versions.length > 0}
        hasStyle={!!style}
        hasStories={savedStories.length > 0}
        layout={t.layout}
        setLayout={(v) => setTweak("layout", v)}
        phase={phase}
        isMobile={isMobile}
      />

      <div className="stage" style={{ "--serif-scale": t.serifScale } as React.CSSProperties}>
        {step === "bible" && phase === "seed" && <SeedScreen seedText={seedText} setSeedText={setSeedText} onBegin={beginGenerate} />}
        {step === "bible" && phase === "thinking" && <Thinking />}
        {step === "bible" && phase === "ready" && view &&
          (effectiveLayout === "manuscript" ? (
            <ManuscriptView key={"ms" + view.id} {...viewProps} />
          ) : (
            <StudioView key={"st" + view.id} {...viewProps} />
          ))}

        {step === "style" && (
          <StyleStage
            world={latestBible}
            worldId={world.id}
            style={style}
            busy={busyStyle}
            onGenerate={onGenerateStyle}
            onRefine={onRefineStyle}
            onAdvance={goStories}
            isMobile={isMobile}
          />
        )}

        {step === "stories" && (
          <StoriesStage
            world={latestBible}
            stories={stories}
            busy={busyStory}
            view={storyView}
            setView={setStoryView}
            onOpen={setEditingStoryId}
            onSave={saveStory}
            onDismiss={dismissStory}
            onProposeMore={proposeMore}
            onAdvance={goFlow}
            bibleVersionLabel={latestBible ? "bible v" + latestBible.n : "the bible"}
          />
        )}

        {step === "flow" && <FlowScreen stories={savedStories} />}

        {sel && !composing && (
          <div className="sel-pop" style={{ left: sel.rect.left, top: sel.rect.top }}>
            <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={openCompose}>
              <Icon name="pen" size={15} /> make a note
            </button>
          </div>
        )}

        {step === "bible" && phase === "ready" && castOpen && (
          <CastPopover
            characters={characters}
            onClose={() => setCastOpen(false)}
            onEdit={editChar}
            onAdd={addCharacter}
            onReweave={reweave}
            dirty={castDirty}
            busy={busy || busyChar}
          />
        )}

        {editingChar && (
          <CharacterEditor
            char={editingChar}
            isNew={newCharId === editingChar.id}
            onClose={() => {
              setEditingId(null);
              setNewCharId(null);
            }}
            onField={onCharField}
            onRefine={onRefineChar}
            onAddTheme={onAddTheme}
            onRemoveTheme={onRemoveTheme}
            onRemove={removeChar}
            busy={busyChar}
          />
        )}

        {editingStory && (
          <StoryEditor
            story={editingStory}
            onClose={() => setEditingStoryId(null)}
            onField={onStoryField}
            onBeat={onStoryBeat}
            onAddBeat={onAddBeat}
            onRemoveBeat={onRemoveBeat}
            onRefine={onRefineStory}
            onSave={saveStory}
            busy={busyStory}
          />
        )}
      </div>

      <TweaksPanel>
        <TweakSection label="Layout direction" />
        <TweakRadio label="Bible canvas" value={t.layout} options={["manuscript", "studio"]} onChange={(v) => setTweak("layout", v)} />
        <TweakSection label="Brand" />
        <TweakColor
          label="Accent"
          value={t.accent}
          options={Object.values(ACCENTS).map((p) => p[0])}
          onChange={(v) => setTweak("accent", v)}
        />
        <TweakToggle label="Paper grain" value={t.grain} onChange={(v) => setTweak("grain", v)} />
        <TweakSection label="Navigation" />
        <TweakButton label="← all worlds" onClick={onHome} />
      </TweaksPanel>
    </div>
  );
}
