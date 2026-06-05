export type WorldTint = "clay" | "sage" | "sky" | "honey" | "rose";
export type Step = "bible" | "style" | "stories" | "flow";
export type Phase = "seed" | "thinking" | "ready";
export type LayoutMode = "manuscript" | "studio";

export interface Para {
  id: string;
  role: string;
  heading: string;
  text: string;
  revised?: boolean;
}

export interface BibleVersion {
  id: string;
  n: number;
  title: string;
  logline: string;
  paras: Para[];
  changeSummary: string;
  basedOn: number | null;
  when: string;
}

export interface Note {
  id: string;
  paraId: string;
  quote: string;
  text: string;
  resolved?: boolean;
  resolvedIn?: number;
}

export type TimelineKind = "seed" | "ask" | "note" | "ai-draft" | "ai-revise";

export interface TimelineEntry {
  kind: TimelineKind;
  text: string;
  quote?: string;
  vN?: number;
}

export interface Character {
  id: string;
  n: number;
  tint: WorldTint;
  name: string;
  role: string;
  bio: string;
  themes: string[];
}

export interface StoryBeat {
  id: string;
  text: string;
}

export interface Story {
  id: string;
  title: string;
  logline: string;
  scenes: number;
  gestures: string[];
  beats: StoryBeat[];
  n: number;
  proposed: boolean;
}

export interface StyleLibrary {
  name: string;
  directionId: string;
  tint: WorldTint;
  medium: string;
  materials: string;
  palette: string[];
  lighting: string;
  camera: string;
  texture: string;
  mood: string;
  negative: string;
  master: string;
  extra: string;
  n: number;
}

export interface World {
  id: string;
  createdAt: number;
  updatedAt: number;
  tint: WorldTint;
  step: Step;
  phase: Phase;
  seed: string;
  versions: BibleVersion[];
  current: number;
  notesByVersion: Record<string, Note[]>;
  timeline: TimelineEntry[];
  stories: Story[];
  characters: Character[];
  castDirty: boolean;
  style: StyleLibrary | null;
  flowStarted: boolean;
}

export interface Tweaks {
  layout: LayoutMode;
  accent: string;
  grain: boolean;
  serifScale: number;
}

export interface SelectionState {
  paraId: string;
  quote: string;
  rect: { left: number; top: number };
}

export interface ComposingState {
  paraId: string;
  quote: string;
}

export type Route =
  | { name: "home" }
  | { name: "world"; worldId: string };

export interface StyleDirection {
  id: string;
  name: string;
  tint: WorldTint;
  thumb: string | null;
  blurb: string;
  medium: string;
  materials: string;
  palette: string[];
  lighting: string;
  camera: string;
  texture: string;
  mood: string;
}

export interface SeedPreset {
  id: string;
  label: string;
  icon: string;
  seed: string;
}
