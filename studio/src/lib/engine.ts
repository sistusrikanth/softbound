import type {
  BibleVersion,
  Character,
  Para,
  SeedPreset,
  Story,
  StyleDirection,
  StyleLibrary,
  WorldTint,
} from "./types";
import * as api from "./api";
import { castSummary, clone, newId } from "./storage";

let apiAvailable: boolean | null = null;

async function useBackend(): Promise<boolean> {
  if (apiAvailable === null) apiAvailable = await api.checkHealth();
  return apiAvailable;
}

export const SEED_PRESETS: SeedPreset[] = [
  {
    id: "meadow",
    label: "rooster meadow",
    icon: "sun",
    seed: "a small meadow where a rooster keeps the day, and the sky turns slowly from morning to night",
  },
  {
    id: "lighthouse",
    label: "the foggy coast",
    icon: "moon",
    seed: "a sleepy lighthouse on a foggy coast, where a small keeper lights a lamp for boats that lose their way",
  },
  {
    id: "river",
    label: "the sleepy river",
    icon: "feather",
    seed: "a little boat that drifts down a slow river, past reeds and sleeping animals, toward a warm harbour",
  },
];

const PRESET_BIBLES: Record<string, { title: string; logline: string; paras: Omit<Para, "id">[] }> = {
  meadow: {
    title: "Rooster meadow",
    logline: "a meadow that breathes from morning into night, one quiet touch at a time.",
    paras: [
      {
        role: "place",
        heading: "the place",
        text: "the meadow sits low and warm, the colour of bread. tall grass leans where the wind last passed. a fence, a single tree, a roof in the distance. nothing hurries here. the light is always the light of late afternoon, even when the moon arrives.",
      },
      {
        role: "who",
        heading: "who lives here",
        text: "a rooster keeps the meadow. he is round and unbothered, the warden of small mornings. in the grass a rabbit waits, and after dark the fireflies wake. none of them ask for attention. they are simply here, the way things in a book are here.",
      },
      {
        role: "touch",
        heading: "what small hands can do",
        text: "the sky is the largest thing to touch. one press and the day folds gently into night, then back again. the rooster will crow if a child asks him to. the bush hides a rabbit who peeks, once, and settles. when the meadow goes dark, the fireflies answer a touch with a slow glow.",
      },
    ],
  },
  lighthouse: {
    title: "The quiet lighthouse",
    logline: "a small keeper, a great lamp, and a coast that waits in the fog.",
    paras: [
      {
        role: "place",
        heading: "the place",
        text: "fog sits on the water like a soft grey blanket. the lighthouse stands at the edge of everything, patient and tall. below it the sea moves slowly, in no hurry to arrive. a gull folds its wings. the air smells of salt and evening.",
      },
      {
        role: "who",
        heading: "who lives here",
        text: "the keeper is small, smaller than the door she opens. she climbs the stairs each evening to wake the lamp. she is not afraid of the dark, only careful with it. a cat keeps her company on the cold steps, and the boats, somewhere out there, are counting on her light.",
      },
      {
        role: "touch",
        heading: "what small hands can do",
        text: "a child wakes the lamp with one touch, and its slow beam reaches into the fog. press the window and a boat finds its way home. press the water and the waves breathe once, then settle. nothing is lost for long here. the light always comes back around.",
      },
    ],
  },
  river: {
    title: "A little boat",
    logline: "a slow drift downriver, past sleeping things, toward a warm harbour.",
    paras: [
      {
        role: "place",
        heading: "the place",
        text: "the river is brown and gentle and in no hurry. it carries a little boat the way a hand carries a sleeping child. reeds lean in to watch it pass. the banks are soft with moss. somewhere ahead there are lights, but the river will get there when it gets there.",
      },
      {
        role: "who",
        heading: "who travels here",
        text: "the boat carries one small passenger and a folded blanket. along the banks the animals are settling: a heron on one leg, a fox curled in the ferns, ducks tucked into themselves. they stir as the boat drifts by, then sleep again. the boat does not wake them. it only passes through.",
      },
      {
        role: "touch",
        heading: "what small hands can do",
        text: "a touch on the water sends one ring outward, slow and round. press a reed and it bows, then rises. press the fox and it opens one eye, then closes it. at the very end the harbour lights come on, one by one, and the boat comes to rest against the warm wood of home.",
      },
    ],
  },
};

function titleFromSeed(seed: string): string {
  const s = seed.toLowerCase();
  const noun = (
    s.match(
      /\b(lighthouse|meadow|forest|river|garden|moon|mountain|harbour|harbor|island|valley|orchard|pond|cottage|hill|sea|snow|desert|cave|nest|burrow|lantern|kite|cloud)\b/,
    ) || []
  )[0];
  if (noun) return "The quiet " + noun.replace("harbor", "harbour");
  return "A small quiet world";
}

function makeBible(seed: string) {
  const clean = (seed || "").trim();
  const subject = clean ? clean.replace(/\.$/, "") : "a small quiet place";
  return {
    title: titleFromSeed(clean),
    logline: "a still place that wakes only when small hands ask it to.",
    paras: [
      {
        role: "place",
        heading: "the place",
        text: `here is ${subject}. it sits in the soft light of late afternoon and does not hurry. the colours are warm and worn, the way a loved page is worn. nothing moves until it is touched, and even then it moves slowly, then settles back into stillness.`,
      },
      {
        role: "who",
        heading: "who lives here",
        text: "someone small keeps this place — gentle, unbothered, easy to love. a few quiet companions share it: things that wait in the grass, things that sleep until evening. none of them ask for attention. they are simply here, the way things in a book are here.",
      },
      {
        role: "touch",
        heading: "what small hands can do",
        text: "every touch is answered, once, and then the world goes still again. press the sky and the light changes. press a small thing and it stirs, peeks, settles. there is no score, no next, no hurry. only the quiet pleasure of making one gentle thing happen, and then another.",
      },
    ],
  };
}

const INTENTS = [
  {
    test: /brave|bold|courage|less afraid|fear/i,
    weave: () => "and braver now — it leans toward the dark instead of away from it, just a little.",
    sum: "braver, leaning toward the dark",
  },
  {
    test: /slow|slower|quiet|calm|gentl|soft/i,
    weave: () => "and slower still — the page waits an extra breath before anything answers.",
    sum: "slower, an extra breath",
  },
  {
    test: /warm|cosy|cozy|home|safe/i,
    weave: () => "and warmer — there is the feeling of a blanket pulled up, of being kept safe.",
    sum: "warmer, a kept feeling",
  },
  {
    test: /add|another|new|second|more.*(animal|friend|character|creature)/i,
    weave: () => "a second small companion waits here too, half-hidden, easy to miss until it is touched.",
    sum: "added a hidden companion",
  },
  {
    test: /colou?r|bright|dusk|golden|evening|light/i,
    weave: () => "the light leans further toward evening gold, the way the world looks just before sleep.",
    sum: "evening gold, before sleep",
  },
  {
    test: /short|less|trim|simpl/i,
    weave: () => "less is said here now; the quiet does the rest.",
    sum: "trimmed, quieter",
  },
  {
    test: /name|call/i,
    weave: (_q: string, note: string) =>
      `it has a name now, the way small things earn names: ${note.replace(/.*name[d]?\s*(it|them)?\s*/i, "").replace(/[".]/g, "").trim() || "something soft and easy to say"}.`,
    sum: "given a gentle name",
  },
];

function reviseBible(prev: BibleVersion, note: { text: string; paraId: string; quote?: string }) {
  const noteText = (note.text || "").trim();
  const intent = INTENTS.find((i) => i.test.test(noteText));
  const paras = prev.paras.map((p) => ({ ...p, revised: false }));
  const targetIdx = Math.max(0, paras.findIndex((p) => p.id === note.paraId));
  const t = paras[targetIdx] || paras[0];
  const woven = intent
    ? intent.weave(note.quote || "", noteText)
    : `we hold your note close — "${noteText}" — and let it settle into the page.`;
  const sep = /[.?!]\s*$/.test(t.text) ? " " : ". ";
  t.text = t.text.replace(/\s+$/, "") + sep + woven;
  t.revised = true;
  const summary = intent ? intent.sum : noteText.split(/\s+/).slice(0, 5).join(" ").toLowerCase() || "a small change";
  return { title: prev.title, logline: prev.logline, paras, summary, changedParaId: t.id };
}

export const STYLE_DIRECTIONS: StyleDirection[] = [
  {
    id: "claymation-meadow",
    name: "Claymation & watercolour",
    tint: "honey",
    thumb: "/brand/styles/claymation-meadow.png",
    blurb: "plasticine figures on watercolour-paper hills, golden-hour warmth.",
    medium: "stop-motion claymation characters composited over hand-painted watercolour scenery",
    materials: "plasticine / polymer clay figures with visible thumbprints; cold-press watercolour paper backgrounds; soft felt foliage",
    palette: ["warm cream sky", "dusty sage hills", "clay terracotta", "muted ochre sun", "soft moss green"],
    lighting: "low golden-hour sun, long soft shadows, gentle haze",
    camera: "shallow depth of field, slight macro tabletop feel, eye-level with the characters",
    texture: "matte clay sheen, paper tooth, subtle paint granulation",
    mood: "calm, warm, hand-made, unhurried",
  },
  {
    id: "paper-diorama",
    name: "Paper diorama theatre",
    tint: "sky",
    thumb: "/brand/styles/paper-diorama.jpg",
    blurb: "layered cut-paper stage set, curtain folds, real depth.",
    medium: "cut-paper diorama built as a miniature theatre stage, photographed straight-on",
    materials: "layered construction paper and cardstock; visible cut edges and curl; corrugated-card stage floor; folded-paper curtains",
    palette: ["deep midnight blue", "leaf green", "kraft brown", "river teal", "paper white highlights"],
    lighting: "soft theatrical front light, gentle shadow between paper layers for depth",
    camera: "flat frontal stage view, layers receding into the dark, slight vignette",
    texture: "matte paper grain, hand-cut edges, layered drop shadows",
    mood: "theatrical, cosy, storybook, quietly grand",
  },
  {
    id: "felt-flannel",
    name: "Felt & flannel board",
    tint: "rose",
    thumb: null,
    blurb: "soft felt shapes on a flannel board, fuzzy and tactile.",
    medium: "felt cut-outs arranged on a flannel storytelling board",
    materials: "wool felt shapes with fuzzy edges; stitched details; flannel backdrop",
    palette: ["oatmeal cream", "dusty rose", "sage", "soft slate", "warm mustard"],
    lighting: "flat soft daylight, minimal shadow",
    camera: "straight-on, flat, picture-book framing",
    texture: "fuzzy felt fibre, visible stitches, matte",
    mood: "soft, tactile, gentle, nursery-warm",
  },
  {
    id: "ink-wash",
    name: "Soft ink & wash",
    tint: "clay",
    thumb: null,
    blurb: "loose ink lines with watercolour wash, lots of paper breathing room.",
    medium: "loose pen-and-ink line drawing with light watercolour washes",
    materials: "dip-pen ink lines; wet-on-wet watercolour; plenty of bare paper",
    palette: ["paper cream", "warm grey ink", "pale honey", "muted teal", "soft blush"],
    lighting: "implied, flat, page-like",
    camera: "picture-book spread framing, generous negative space",
    texture: "ink bleed, paper grain, soft wash edges",
    mood: "airy, quiet, literary, hand-drawn",
  },
];

function styleLibraryFor(dir: StyleDirection, extra: string, world: BibleVersion | null): StyleLibrary {
  const subject = world ? world.title : "this world";
  const master = `${dir.medium}. ${dir.materials}. Scene: ${subject.toLowerCase()}${extra ? ", " + extra.trim() : ""}. Palette: ${dir.palette.join(", ")}. Lighting: ${dir.lighting}. ${dir.camera}. Texture: ${dir.texture}. Mood: ${dir.mood}. Calming non-stimulating children's picture-book illustration, no text, no busy detail, single clear subject.`;
  return {
    name: dir.name,
    directionId: dir.id,
    tint: dir.tint,
    medium: dir.medium,
    materials: dir.materials,
    palette: dir.palette,
    lighting: dir.lighting,
    camera: dir.camera,
    texture: dir.texture,
    mood: dir.mood,
    negative: "no text, no logos, no busy backgrounds, no harsh contrast, no neon, no clutter, no scary faces",
    master,
    extra: extra || "",
    n: 1,
  };
}

const STORY_SEEDS = [
  { t: "the first light", l: "the world wakes, slowly, and learns it is safe to be touched.", scenes: 4, g: ["tap", "press"] },
  { t: "the long afternoon", l: "one quiet game, repeated, the way small children love repetition.", scenes: 5, g: ["tap", "swipe"] },
  { t: "into the evening", l: "the light folds toward night; everything settles, one creature at a time.", scenes: 6, g: ["tap", "long press"] },
  { t: "the small lost thing", l: "something is misplaced, and found, without ever being frightening.", scenes: 5, g: ["tap", "drag"] },
  { t: "everyone is sleepy", l: "one by one, each friend finds a place to rest.", scenes: 6, g: ["tap", "long press"] },
  { t: "the visiting weather", l: "rain, then sun; the world changes gently and changes back.", scenes: 4, g: ["tap", "tilt"] },
  { t: "a game of peek", l: "things hide and reappear, the oldest, softest game.", scenes: 4, g: ["tap", "swipe"] },
  { t: "the quiet parade", l: "the friends walk together, slowly, to nowhere in particular.", scenes: 5, g: ["tap", "drag"] },
];

function defaultBeats(_title: string, n: number) {
  const base = [
    "the world is still, waiting",
    "a small hand reaches in",
    "something gently stirs",
    "it settles, changed a little",
    "the world is still again",
  ];
  return base.slice(0, Math.max(3, Math.min(n, 5))).map((b) => ({ id: newId("b"), text: b }));
}

function proposeStoriesConditioned(_bible: BibleVersion | null, existing: Story[], count: number): Story[] {
  const taken = new Set((existing || []).map((s) => s.title.toLowerCase()));
  const pool = STORY_SEEDS.filter((s) => !taken.has(s.t.toLowerCase()));
  return pool.slice(0, count || 3).map((s) => ({
    id: newId("story"),
    title: s.t,
    logline: s.l,
    scenes: s.scenes,
    gestures: s.g,
    beats: defaultBeats(s.t, s.scenes),
    n: 1,
    proposed: true,
  }));
}

const TINTS: WorldTint[] = ["clay", "sage", "sky", "honey", "rose"];

const PRESET_CASTS: Record<string, Omit<Character, "id" | "n">[]> = {
  meadow: [
    {
      name: "Rooster",
      role: "warden of small mornings",
      tint: "clay",
      bio: "round and unbothered, he keeps the meadow's hours. he crows only when a child asks him to, then settles back into the grass.",
      themes: ["morning", "routine", "gentle authority"],
    },
    {
      name: "Rabbit",
      role: "the one who waits",
      tint: "sage",
      bio: "tucked in the bush, she peeks out once when touched, then is still again. she is the meadow's small, soft surprise.",
      themes: ["patience", "hiding", "curiosity"],
    },
    {
      name: "Fireflies",
      role: "the evening glow",
      tint: "honey",
      bio: "they sleep through the day and answer a touch after dark with a slow, warm light. they ask for nothing back.",
      themes: ["night", "wonder", "settling"],
    },
  ],
  lighthouse: [
    {
      name: "The keeper",
      role: "small, careful with the dark",
      tint: "clay",
      bio: "smaller than the door she opens, she climbs each evening to wake the lamp. she is not afraid of the dark, only careful with it.",
      themes: ["care", "courage", "light"],
    },
    {
      name: "The cat",
      role: "company on cold steps",
      tint: "sky",
      bio: "keeps the keeper company on the long climb. warm, quiet, easy to have near. it watches the fog with her and says nothing.",
      themes: ["comfort", "quiet", "warmth"],
    },
  ],
  river: [
    {
      name: "The little boat",
      role: "carries one small passenger",
      tint: "sky",
      bio: "drifts down the slow river with a folded blanket aboard. it is in no hurry, and it does not wake the sleeping banks.",
      themes: ["drifting", "calm", "journey"],
    },
    {
      name: "The heron",
      role: "stands on one leg",
      tint: "sage",
      bio: "watches the boat pass from the reeds, then tucks its head again. it is the stillest thing on the whole river.",
      themes: ["stillness", "watching"],
    },
    {
      name: "The fox",
      role: "curled in the ferns",
      tint: "rose",
      bio: "opens one eye when a child touches it, then closes it. asleep again before the boat has fully drifted by.",
      themes: ["sleep", "gentleness"],
    },
  ],
};

function withCharIds(list: Omit<Character, "id" | "n">[]): Character[] {
  return list.map((c, i) => ({
    ...c,
    id: newId("c"),
    n: 1,
    tint: c.tint || TINTS[i % TINTS.length],
  }));
}

function makeCast(seed: string): Character[] {
  const subject = (seed || "").trim() || "this world";
  return withCharIds([
    {
      name: "the keeper",
      role: "the one who tends this place",
      tint: "clay",
      bio: `someone small looks after ${subject} — gentle, unhurried, easy to love. they ask for nothing and answer every touch, once, then settle.`,
      themes: ["care", "calm"],
    },
    {
      name: "a quiet companion",
      role: "the small surprise",
      tint: "sage",
      bio: "waits half-hidden until a child reaches out, then peeks, stirs, and folds back into stillness. easy to miss, lovely to find.",
      themes: ["patience", "wonder"],
    },
  ]);
}

const CHAR_INTENTS = [
  { test: /brave|bold|courage|less afraid|fear/i, add: "courage", line: "braver now — they lean toward the dark a little, instead of away from it." },
  { test: /slow|slower|calm|gentl|soft|quiet/i, add: "calm", line: "calmer now — they move a half-beat slower than they did before." },
  { test: /warm|cosy|cozy|kind|tender/i, add: "warmth", line: "warmer now — there is a kept, blanket-pulled-up feeling around them." },
  { test: /curious|wonder|explore|notice/i, add: "curiosity", line: "more curious now — they notice the small things a child would notice." },
  { test: /play|funny|mischie|silly/i, add: "mischief", line: "a little more playful now — a small, quiet mischief has crept in." },
  { test: /old|wise|gentle.*age|grandmother|grandfather/i, add: "wisdom", line: "older and gentler now, the way a well-loved grandparent is gentle." },
];

function reviseCharacter(prev: Character, noteText: string): Character {
  const t = (noteText || "").trim();
  const intent = CHAR_INTENTS.find((i) => i.test.test(t));
  const sep = /[.?!]\s*$/.test(prev.bio) ? " " : ". ";
  const line = intent ? "they are " + intent.line : `they carry your note now — "${t}".`;
  const bio = prev.bio.replace(/\s+$/, "") + sep + line;
  const themes = intent && !prev.themes.includes(intent.add) ? [...prev.themes, intent.add] : prev.themes;
  return { ...prev, bio, themes, n: (prev.n || 1) + 1 };
}

export async function aiGenerate(seed: string, presetId: string | null) {
  if (presetId && PRESET_BIBLES[presetId]) return clone(PRESET_BIBLES[presetId]);
  if (await useBackend()) {
    try {
      return await api.generateBible(seed, presetId);
    } catch (e) {
      console.warn("API bible generate failed, using local fallback:", e);
    }
  }
  return makeBible(seed);
}

export async function aiRevise(prev: BibleVersion, note: { text: string; paraId: string; quote?: string }) {
  if (await useBackend()) {
    try {
      return await api.reviseBible(prev, note);
    } catch (e) {
      console.warn("API bible revise failed, using local fallback:", e);
    }
  }
  return reviseBible(prev, note);
}

export async function aiStyleLibrary(world: BibleVersion | null, dir: StyleDirection, extra: string, n = 1) {
  if (await useBackend()) {
    try {
      return await api.generateStyleLibrary(world, dir, extra, n);
    } catch (e) {
      console.warn("API style generate failed, using local fallback:", e);
    }
  }
  return styleLibraryFor(dir, extra, world);
}

export async function aiProposeStories(bible: BibleVersion | null, existing: Story[], count: number) {
  if (await useBackend()) {
    try {
      return await api.proposeStories(bible, existing, count);
    } catch (e) {
      console.warn("API story propose failed, using local fallback:", e);
    }
  }
  return proposeStoriesConditioned(bible, existing, count);
}

export async function aiReviseStory(story: Story, askText: string): Promise<Story> {
  if (await useBackend()) {
    try {
      return await api.reviseStory(story, askText);
    } catch (e) {
      console.warn("API story revise failed, using local fallback:", e);
    }
  }
  return { ...story, logline: story.logline + " " + askText.trim(), n: (story.n || 1) + 1 };
}

export async function aiSeedCharacters(seed: string, presetId: string | null): Promise<Character[]> {
  if (presetId && PRESET_CASTS[presetId]) return withCharIds(clone(PRESET_CASTS[presetId]));
  if (await useBackend()) {
    try {
      return await api.seedCharacters(seed, presetId);
    } catch (e) {
      console.warn("API cast seed failed, using local fallback:", e);
    }
  }
  return makeCast(seed);
}

export async function aiReviseCharacter(prev: Character, noteText: string): Promise<Character> {
  if (await useBackend()) {
    try {
      return await api.refineCharacter(prev, noteText);
    } catch (e) {
      console.warn("API character refine failed, using local fallback:", e);
    }
  }
  return reviseCharacter(prev, noteText);
}

export async function aiFleshCharacter(prev: Character, seedText: string): Promise<Character> {
  if (await useBackend()) {
    try {
      return await api.fleshCharacter(prev, seedText);
    } catch (e) {
      console.warn("API character flesh failed, using local fallback:", e);
    }
  }
  const subj = seedText.trim();
  return {
    ...prev,
    name: subj.split(/\s+/).slice(0, 2).join(" ") || prev.name,
    role: "a new presence",
    bio: `${subj} joins this world — quiet, unhurried, answering a small hand and then settling back into stillness.`,
    themes: ["calm"],
    n: 1,
  };
}

export async function aiRegenWithCast(prev: BibleVersion, chars: Character[]) {
  if (await useBackend()) {
    try {
      return await api.reweaveBible(prev, chars);
    } catch (e) {
      console.warn("API bible reweave failed, using local fallback:", e);
    }
  }
  const paras = prev.paras.map((p) => ({ ...p, revised: false }));
  let idx = paras.findIndex((p) => p.role === "who");
  if (idx < 0) idx = Math.min(1, paras.length - 1);
  const intro = chars.map((c) => `${c.name.toLowerCase()}, ${c.role}`).join("; ");
  paras[idx] = {
    ...paras[idx],
    revised: true,
    text: `${castSummary(chars)} share this place — ${intro}. none of them ask for attention. they are simply here, the way things in a book are here, waiting for a small hand to reach out.`,
  };
  return { title: prev.title, logline: prev.logline, paras, summary: "rewoven with the cast" };
}
