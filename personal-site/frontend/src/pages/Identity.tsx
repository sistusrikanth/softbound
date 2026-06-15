import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { usePrivateToken } from "../lib/auth";
import PrivateShell from "../components/PrivateShell";
import type { IdentityCard } from "../lib/types";
import "./PrivatePages.css";

const CORE_CATEGORIES = ["who_i_am", "what_i_do", "what_i_care_about"] as const;
const SITE_CATEGORIES = ["writing", "systems", "photography", "projects"] as const;

const LABELS: Record<string, string> = {
  who_i_am: "Who I am",
  what_i_do: "What I do",
  what_i_care_about: "What I care about",
  writing: "Writing",
  systems: "Systems",
  photography: "Photography",
  projects: "Projects",
};

const HINTS: Record<string, string> = {
  who_i_am: "The essence — who you are when stripped to a few lines.",
  what_i_do: "How you spend your days and what you're known for.",
  what_i_care_about: "Values and principles that guide decisions.",
  writing: "The face of your writing section — what visitors should feel.",
  systems: "The face of your systems work — your design philosophy.",
  photography: "The face of your photography — your eye in a sentence.",
  projects: "The face of your projects — what you're building toward.",
};

export default function IdentityPage() {
  const token = usePrivateToken();
  const [cards, setCards] = useState<IdentityCard[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState<string | null>(null);

  const load = async () => {
    const list = await api.getIdentityCards(token);
    setCards(list);
    const d: Record<string, string> = {};
    for (const c of list) d[c.category] = c.content;
    setDrafts(d);
  };

  useEffect(() => {
    load().catch(() => {});
  }, [token]);

  const handleSave = async (category: string) => {
    await api.updateIdentityCard(token, category, drafts[category] || "");
    setSaved(category);
    await load();
    setTimeout(() => setSaved(null), 2000);
  };

  const renderSection = (title: string, categories: readonly string[]) => (
    <section className="identity-section">
      <h2 className="mono identity-section-title">{title}</h2>
      <div className="identity-cards">
        {categories.map((cat) => (
          <div key={cat} className="identity-card card">
            <div className="identity-card-header">
              <h3 className="serif">{LABELS[cat]}</h3>
              <p className="identity-hint">{HINTS[cat]}</p>
            </div>
            <textarea
              value={drafts[cat] || ""}
              onChange={(e) => setDrafts({ ...drafts, [cat]: e.target.value })}
              rows={3}
              placeholder="A few lines that remind you…"
            />
            <button
              type="button"
              className="btn btn-outline identity-save"
              onClick={() => handleSave(cat)}
            >
              {saved === cat ? "Saved ✓" : "Save"}
            </button>
          </div>
        ))}
      </div>
    </section>
  );

  return (
    <PrivateShell>
      <p className="section-label"><span>§</span> Private Who I am</p>
      <h1 className="page-title serif">Remember who you are.</h1>
      <p className="page-subtitle">
        A few lines per category — the core of your identity and the face of each section on your site.
        Read this when you lose the thread.
      </p>

      {cards.length === 0 ? (
        <p className="mono private-muted">Loading…</p>
      ) : (
        <>
          {renderSection("Core", CORE_CATEGORIES)}
          {renderSection("Site face", SITE_CATEGORIES)}
        </>
      )}
    </PrivateShell>
  );
}
