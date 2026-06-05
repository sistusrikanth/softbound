import type { World } from "./types";

export const LIB_KEY = "softbound:worlds:v2";

export function loadLibrary(): World[] {
  try {
    const s = JSON.parse(localStorage.getItem(LIB_KEY) || "");
    if (s && Array.isArray(s.worlds)) return s.worlds as World[];
  } catch {
    /* ignore */
  }
  try {
    const old = JSON.parse(localStorage.getItem("softbound:wb:v1") || "");
    if (old && Array.isArray(old.versions) && old.versions.length) {
      return [
        {
          ...blankWorld(),
          ...old,
          id: newId("w"),
          style: old.style || null,
          flowStarted: false,
        } as World,
      ];
    }
  } catch {
    /* ignore */
  }
  return [];
}

export function saveLibrary(worlds: World[]): void {
  localStorage.setItem(LIB_KEY, JSON.stringify({ worlds }));
}

export function newId(prefix = "id"): string {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export const TINTS = ["clay", "sage", "sky", "honey", "rose"] as const;

export function blankWorld(): World {
  const tint = TINTS[Math.floor(Math.random() * TINTS.length)];
  return {
    id: newId("w"),
    createdAt: Date.now(),
    updatedAt: Date.now(),
    tint,
    step: "bible",
    phase: "seed",
    seed: "",
    versions: [],
    current: 0,
    notesByVersion: {},
    timeline: [],
    stories: [],
    characters: [],
    castDirty: false,
    style: null,
    flowStarted: false,
  };
}

export function clockNow(): string {
  return new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export function clone<T>(o: T): T {
  return JSON.parse(JSON.stringify(o));
}

export function castSummary(chars: { name: string }[]): string {
  const names = chars.map((c) => c.name.toLowerCase());
  if (names.length <= 1) return names[0] || "";
  return names.slice(0, -1).join(", ") + " and " + names[names.length - 1];
}

export function withParaIds(bible: { title: string; logline: string; paras: Omit<import("./types").Para, "id">[] }) {
  return {
    ...bible,
    paras: bible.paras.map((p) => ({ ...p, id: newId("p") })),
  };
}

export function makeVersion(
  bible: { title: string; logline: string; paras: import("./types").Para[] },
  meta: { n: number; changeSummary: string; basedOn?: number | null },
): import("./types").BibleVersion {
  return {
    id: newId("v"),
    n: meta.n,
    title: bible.title,
    logline: bible.logline,
    paras: bible.paras,
    changeSummary: meta.changeSummary,
    basedOn: meta.basedOn ?? null,
    when: clockNow(),
  };
}
