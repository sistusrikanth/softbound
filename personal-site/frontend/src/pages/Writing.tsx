import { Link } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { api, categoryLabel, formatDate } from "../lib/api";
import type { Article } from "../lib/types";
import "./Writing.css";

const CATEGORIES = ["all", "papers", "systems", "notes"] as const;

export default function WritingPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    api.getArticles().then(setArticles);
  }, []);

  const featured = articles.find((a) => a.featured);
  const filtered = useMemo(() => {
    if (filter === "all") return articles.filter((a) => !a.featured || articles.filter((x) => x.featured).length === articles.length);
    return articles.filter((a) => a.category === filter);
  }, [articles, filter]);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: articles.length };
    for (const cat of ["papers", "systems", "notes"]) {
      c[cat] = articles.filter((a) => a.category === cat).length;
    }
    return c;
  }, [articles]);

  return (
    <div className="writing-page">
      <p className="section-label"><span>§</span> Writing Writing</p>
      <h1 className="page-title serif">Papers, taken apart.</h1>
      <p className="page-subtitle">
        I read research papers and rebuild them from their core components — the wiring made visible, the jargon removed.
      </p>

      {featured && (
        <Link to={`/writing/${featured.slug}`} className="featured-card card">
          <span className="featured-label mono">Featured paper</span>
          <h2 className="featured-title serif">{featured.title}</h2>
          <p className="featured-summary">{featured.summary}</p>
          <div className="featured-footer">
            <span className="tag">{featured.tags.split(",")[0]}</span>
            <span className="mono featured-meta">{formatDate(featured.created_at)}</span>
            <span className="mono featured-meta">{featured.read_time_min} min</span>
          </div>
        </Link>
      )}

      <div className="filter-bar">
        {CATEGORIES.map((cat) => (
          <button key={cat} className={filter === cat ? "active" : ""} onClick={() => setFilter(cat)}>
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
            <span>{counts[cat] || 0}</span>
          </button>
        ))}
      </div>

      <div className="article-grid">
        {filtered.map((a) => (
          <Link key={a.id} to={`/writing/${a.slug}`} className="article-card card">
            <div className="article-card-top">
              <span className={`article-type mono type-${a.category}`}>{categoryLabel(a.category)}</span>
              <span className="mono article-time">{a.read_time_min} min</span>
            </div>
            <h3 className="article-card-title serif">{a.title}</h3>
            <p className="article-card-summary">{a.summary}</p>
            <div className="article-card-footer">
              <span className="tag">{a.tags.split(",")[0]}</span>
              <span className="mono article-date">{formatDate(a.created_at)}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
