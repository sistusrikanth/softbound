import type {
  Article,
  DayEntry,
  Experience,
  ExperienceProjectDetail,
  IdentityCard,
  PhotoLink,
  Project,
  SiteConfig,
  StartupIdea,
  WeekSummary,
} from "./types";

const API = "/api";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

export const api = {
  getConfig: () => fetchJson<SiteConfig>(`${API}/config`),

  getArticles: (category?: string) =>
    fetchJson<Article[]>(`${API}/articles${category ? `?category=${category}` : ""}`),

  getFeaturedArticle: () => fetchJson<Article[]>(`${API}/articles?featured=true`),

  getArticle: (slug: string) => fetchJson<Article>(`${API}/articles/${slug}`),

  getPhotos: (category?: string) =>
    fetchJson<PhotoLink[]>(`${API}/photos${category ? `?category=${category}` : ""}`),

  getProjects: () => fetchJson<Project[]>(`${API}/projects`),

  getIdeas: () => fetchJson<StartupIdea[]>(`${API}/ideas`),

  login: (password: string) =>
    fetchJson<{ access_token: string }>(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    }),

  adminGetArticles: (token: string) =>
    fetchJson<Article[]>(`${API}/admin/articles`, { headers: authHeaders(token) }),

  createArticle: (token: string, data: Partial<Article>) =>
    fetchJson<Article>(`${API}/admin/articles`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify(data),
    }),

  updateArticle: (token: string, id: number, data: Partial<Article>) =>
    fetchJson<Article>(`${API}/admin/articles/${id}`, {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify(data),
    }),

  deleteArticle: (token: string, id: number) =>
    fetchJson<{ ok: boolean }>(`${API}/admin/articles/${id}`, {
      method: "DELETE",
      headers: authHeaders(token),
    }),

  uploadAttachment: async (token: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/admin/uploads`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json() as Promise<{ url: string; filename: string; kind: "image" | "excalidraw" }>;
  },

  createPhoto: (token: string, data: { title: string; instagram_url: string; category: string }) =>
    fetchJson<PhotoLink>(`${API}/admin/photos`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify(data),
    }),

  deletePhoto: (token: string, id: number) =>
    fetchJson<{ ok: boolean }>(`${API}/admin/photos/${id}`, {
      method: "DELETE",
      headers: authHeaders(token),
    }),

  getDayEntries: (token: string) =>
    fetchJson<DayEntry[]>(`${API}/admin/days`, { headers: authHeaders(token) }),

  getDayEntry: (token: string, date: string) =>
    fetchJson<DayEntry>(`${API}/admin/days/${date}`, { headers: authHeaders(token) }),

  saveDayEntry: (token: string, date: string, data: { personal: string; professional: string }) =>
    fetchJson<DayEntry>(`${API}/admin/days/${date}`, {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify({ entry_date: date, ...data }),
    }),

  deleteDayEntry: (token: string, date: string) =>
    fetchJson<{ ok: boolean }>(`${API}/admin/days/${date}`, {
      method: "DELETE",
      headers: authHeaders(token),
    }),

  getWeekSummary: (token: string, weekStart: string) =>
    fetchJson<WeekSummary>(`${API}/admin/weeks/${weekStart}`, { headers: authHeaders(token) }),

  updateWeekSummary: (token: string, weekStart: string, summary: string) =>
    fetchJson<WeekSummary>(`${API}/admin/weeks/${weekStart}/summary`, {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify({ summary }),
    }),

  getExperience: () => fetchJson<Experience>(`${API}/experience`),

  getExperienceProject: (slug: string) =>
    fetchJson<ExperienceProjectDetail>(`${API}/experience/projects/${slug}`),

  getIdentityCards: (token: string) =>
    fetchJson<IdentityCard[]>(`${API}/admin/identity`, { headers: authHeaders(token) }),

  updateIdentityCard: (token: string, category: string, content: string) =>
    fetchJson<IdentityCard>(`${API}/admin/identity/${category}`, {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify({ content }),
    }),
};

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

export function categoryLabel(cat: string): string {
  const map: Record<string, string> = {
    papers: "PAPER",
    systems: "SYSTEMS",
    notes: "NOTE",
  };
  return map[cat] || cat.toUpperCase();
}
