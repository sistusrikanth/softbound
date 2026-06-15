import { Link, useOutletContext } from "react-router-dom";
import { useEffect, useState } from "react";
import { api, formatDate } from "../lib/api";
import type { Article, SiteConfig } from "../lib/types";
import "./Index.css";

export default function IndexPage() {
  const config = useOutletContext<SiteConfig>();
  const [articles, setArticles] = useState<Article[]>([]);
  const [counts, setCounts] = useState({ writing: 0, systems: 0, photos: 0, projects: 0 });

  useEffect(() => {
    Promise.all([api.getArticles(), api.getPhotos(), api.getProjects()]).then(([arts, photos, projects]) => {
      setArticles(arts.slice(0, 5));
      setCounts({
        writing: arts.length,
        systems: arts.filter((a) => a.category === "systems").length,
        photos: photos.length,
        projects: projects.length,
      });
    });
  }, []);

  const exploreCards = [
    { num: "01", icon: "✎", title: "Writing", desc: "Research papers, taken apart and rebuilt from their core components.", to: "/writing", count: `${counts.writing} essays` },
    { num: "02", icon: "◈", title: "Systems", desc: "Designing the ML systems everyone uses — and showing the reasoning.", to: "/systems", count: `${counts.systems} designs` },
    { num: "03", icon: "◎", title: "Photography", desc: "A working portfolio. Cities, light, and the occasional whiteboard.", to: "/photography", count: `${counts.photos} frames` },
    { num: "04", icon: "{ }", title: "Code", desc: "Small, sharp pieces — annotated line by line.", to: "/writing?category=notes", count: "snippets" },
    { num: "05", icon: "↗", title: "Projects", desc: "Things I'm building and startup ideas I can't stop thinking about.", to: "/projects", count: `${counts.projects} active` },
  ];

  return (
    <div className="index-page">
      <p className="index-eyebrow mono">Writer + ML Systems + Photography</p>
      <h1 className="index-hero serif">I break complex systems down to their essence.</h1>
      <p className="index-intro">
        I read the research so the ideas show through, design machine-learning systems in the open,
        and photograph the world in between.
      </p>

      <div className="index-cta">
        <Link to="/writing" className="btn btn-primary">Read the writing →</Link>
        <Link to="/projects" className="btn btn-outline">See what I'm building</Link>
      </div>

      <p className="index-location mono">
        <span className="index-avatar">●</span>
        {config.name} — based in {config.location}
      </p>

      <section className="index-explore">
        <h2 className="index-section-title mono">Explore the work</h2>
        <div className="index-grid">
          {exploreCards.map((card) => (
            <Link key={card.num} to={card.to} className="index-card card">
              <div className="index-card-top">
                <span className="index-card-icon">{card.icon}</span>
                <span className="index-card-num mono">{card.num}</span>
              </div>
              <h3 className="index-card-title">{card.title}</h3>
              <p className="index-card-desc">{card.desc}</p>
              <div className="index-card-footer mono">
                <span>{card.count}</span>
                <span>→</span>
              </div>
            </Link>
          ))}
          <div className="index-card index-card-now card">
            <span className="index-now-badge mono">NOW</span>
            <p className="index-now-text">{config.now_text}</p>
          </div>
        </div>
      </section>

      <section className="index-recent">
        <div className="index-recent-header">
          <h2 className="mono">Recent writing</h2>
          <Link to="/writing" className="mono">All {counts.writing} →</Link>
        </div>
        <div className="index-recent-list">
          {articles.map((a) => (
            <Link key={a.id} to={`/writing/${a.slug}`} className="index-recent-row">
              <span className="mono index-recent-date">{formatDate(a.created_at)}</span>
              <span className="index-recent-title serif">{a.title}</span>
              <span className="tag">{a.tags.split(",")[0]}</span>
              <span className="mono index-recent-time">{a.read_time_min} min</span>
              <span className="index-recent-arrow">→</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
