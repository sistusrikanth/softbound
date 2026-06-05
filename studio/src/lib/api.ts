import type { BibleVersion, Character, Para, Story, StyleDirection, StyleLibrary, WorldTint } from "./types";
import { newId, TINTS } from "./storage";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function callApi<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const message =
      (err as { detail?: { detail?: string; error?: string } })?.detail?.detail ??
      (err as { detail?: { error?: string } })?.detail?.error ??
      `Request failed (${res.status})`;
    throw new ApiError(message);
  }

  return res.json() as Promise<T>;
}

let healthCache: { ok: boolean; at: number } | null = null;

export async function checkHealth(force = false): Promise<boolean> {
  if (!force && healthCache && Date.now() - healthCache.at < 30_000) {
    return healthCache.ok;
  }
  try {
    const res = await fetch(`${API_BASE}/health`);
    const ok = res.ok;
    healthCache = { ok, at: Date.now() };
    return ok;
  } catch {
    healthCache = { ok: false, at: Date.now() };
    return false;
  }
}

type ApiBible = { title: string; logline: string; paras: Omit<Para, "id">[] };
type ApiCharacter = { name: string; role: string; bio: string; themes: string[]; tint?: WorldTint };
type ApiStory = {
  title: string;
  logline: string;
  scenes: number;
  gestures: string[];
  beats: { text: string }[];
};

function bibleToApi(bible: BibleVersion) {
  return {
    title: bible.title,
    logline: bible.logline,
    paras: bible.paras.map((p) => ({ role: p.role, heading: p.heading, text: p.text })),
  };
}

function mapCharacters(raw: ApiCharacter[]): Character[] {
  return raw.map((c, i) => ({
    id: newId("c"),
    n: 1,
    tint: c.tint || TINTS[i % TINTS.length],
    name: c.name,
    role: c.role,
    bio: c.bio,
    themes: c.themes || [],
  }));
}

function mapStories(raw: ApiStory[]): Story[] {
  return raw.map((s) => ({
    id: newId("story"),
    title: s.title,
    logline: s.logline,
    scenes: s.scenes,
    gestures: s.gestures || ["tap"],
    beats: (s.beats || []).map((b) => ({ id: newId("b"), text: b.text })),
    n: 1,
    proposed: true,
  }));
}

function mapStyle(raw: Record<string, unknown>, dir: StyleDirection, extra: string, n: number): StyleLibrary {
  return {
    name: (raw.name as string) || dir.name,
    directionId: (raw.direction_id as string) || dir.id,
    tint: ((raw.tint as WorldTint) || dir.tint) as WorldTint,
    medium: (raw.medium as string) || dir.medium,
    materials: (raw.materials as string) || dir.materials,
    palette: (raw.palette as string[]) || dir.palette,
    lighting: (raw.lighting as string) || dir.lighting,
    camera: (raw.camera as string) || dir.camera,
    texture: (raw.texture as string) || dir.texture,
    mood: (raw.mood as string) || dir.mood,
    negative: (raw.negative as string) || "no text, no clutter, no harsh contrast",
    master: (raw.master as string) || "",
    extra,
    n,
  };
}

export async function generateBible(seed: string, presetId: string | null): Promise<ApiBible> {
  const data = await callApi<{ bible: ApiBible }>("/api/studio/bible/generate", {
    seed,
    preset_id: presetId,
  });
  return data.bible;
}

export async function reviseBible(
  bible: BibleVersion,
  note: { text: string; paraId: string; quote?: string },
): Promise<{ title: string; logline: string; paras: Omit<Para, "id">[]; summary: string }> {
  return callApi("/api/studio/bible/revise", {
    bible: bibleToApi(bible),
    note: { text: note.text, quote: note.quote || "", para_id: note.paraId },
  });
}

export async function reweaveBible(
  bible: BibleVersion,
  characters: Character[],
): Promise<{ title: string; logline: string; paras: Omit<Para, "id">[]; summary: string }> {
  return callApi("/api/studio/bible/reweave", {
    bible: bibleToApi(bible),
    characters: characters.map((c) => ({
      name: c.name,
      role: c.role,
      bio: c.bio,
      themes: c.themes,
    })),
  });
}

export async function seedCharacters(seed: string, presetId: string | null): Promise<Character[]> {
  const data = await callApi<{ characters: ApiCharacter[] }>("/api/studio/cast/seed", {
    seed,
    preset_id: presetId,
    count: 3,
  });
  return mapCharacters(data.characters);
}

export async function refineCharacter(character: Character, ask: string): Promise<Character> {
  const data = await callApi<{ character: ApiCharacter }>("/api/studio/characters/refine", {
    character: {
      name: character.name,
      role: character.role,
      bio: character.bio,
      themes: character.themes,
      tint: character.tint,
    },
    ask,
  });
  return {
    ...character,
    role: data.character.role || character.role,
    bio: data.character.bio || character.bio,
    themes: data.character.themes || character.themes,
    n: (character.n || 1) + 1,
  };
}

export async function fleshCharacter(character: Character, seed: string): Promise<Character> {
  const data = await callApi<{ character: ApiCharacter }>("/api/studio/characters/flesh", {
    character: { name: character.name, role: character.role, bio: character.bio, themes: character.themes },
    seed,
  });
  return {
    ...character,
    name: data.character.name || character.name,
    role: data.character.role || character.role,
    bio: data.character.bio || character.bio,
    themes: data.character.themes || [],
    n: 1,
  };
}

export async function generateStyleLibrary(
  bible: BibleVersion | null,
  dir: StyleDirection,
  extra: string,
  n: number,
): Promise<StyleLibrary> {
  const data = await callApi<{ style: Record<string, unknown> }>("/api/studio/style/generate", {
    bible: bible ? bibleToApi(bible) : { title: "", logline: "", paras: [] },
    direction: {
      id: dir.id,
      name: dir.name,
      tint: dir.tint,
      blurb: dir.blurb,
      medium: dir.medium,
      materials: dir.materials,
      palette: dir.palette,
      lighting: dir.lighting,
      camera: dir.camera,
      texture: dir.texture,
      mood: dir.mood,
    },
    extra,
  });
  return mapStyle(data.style, dir, extra, n);
}

export async function proposeStories(bible: BibleVersion | null, existing: Story[], count: number): Promise<Story[]> {
  const data = await callApi<{ stories: ApiStory[] }>("/api/studio/stories/propose", {
    bible: bible ? bibleToApi(bible) : { title: "", logline: "", paras: [] },
    existing: existing.map((s) => ({ title: s.title, logline: s.logline })),
    count,
  });
  return mapStories(data.stories);
}

export async function reviseStory(story: Story, ask: string): Promise<Story> {
  const data = await callApi<{ story: ApiStory }>("/api/studio/stories/revise", {
    story: {
      title: story.title,
      logline: story.logline,
      beats: (story.beats || []).map((b) => ({ text: b.text })),
    },
    ask,
  });
  const s = data.story;
  return {
    ...story,
    title: s.title || story.title,
    logline: s.logline || story.logline,
    beats: (s.beats || []).map((b) => ({ id: newId("b"), text: b.text })),
    scenes: (s.beats || []).length,
    n: (story.n || 1) + 1,
  };
}

export async function expandDescription(description: string, worldStyle = ""): Promise<string> {
  const data = await callApi<{ description: string }>("/api/expand-description", {
    description,
    world_style: worldStyle,
    characters: [],
  });
  return data.description;
}
