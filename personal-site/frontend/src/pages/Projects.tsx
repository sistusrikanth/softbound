import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Project, StartupIdea } from "../lib/types";
import "./Projects.css";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [ideas, setIdeas] = useState<StartupIdea[]>([]);

  useEffect(() => {
    Promise.all([api.getProjects(), api.getIdeas()]).then(([p, i]) => {
      setProjects(p);
      setIdeas(i);
    });
  }, []);

  return (
    <div className="projects-page">
      <p className="section-label"><span>§</span> Projects Projects</p>
      <h1 className="page-title serif">Things I'm building.</h1>
      <p className="page-subtitle">
        A few of these are real and shipping. The rest are startup ideas I can't stop thinking about — take one if it speaks to you.
      </p>

      <div className="project-grid">
        {projects.map((p) => (
          <a key={p.id} href={p.url || "#"} className="project-card card" target={p.url.startsWith("http") ? "_blank" : undefined} rel="noopener noreferrer">
            <div className="project-card-top">
              <span className="project-icon" style={{ background: p.icon_color }} />
              <span className={`project-status mono status-${p.status}`}>
                ● {p.status.toUpperCase()}
              </span>
            </div>
            <h3 className="project-title">{p.title}</h3>
            <p className="project-desc">{p.description}</p>
            <div className="project-footer">
              <div className="project-tags mono">
                {p.tech_tags.split(",").filter(Boolean).map((t) => (
                  <span key={t} className="tech-tag">{t.trim()}</span>
                ))}
              </div>
              <span className="project-arrow">↗</span>
            </div>
          </a>
        ))}
      </div>

      <section className="ideas-section">
        <p className="section-label"><span>§</span> Ideas Startup ideas — unclaimed</p>
        <div className="ideas-list">
          {ideas.map((idea, i) => (
            <div key={idea.id} className="idea-row">
              <div className="idea-content">
                <span className="idea-num mono">{String(i + 1).padStart(2, "0")}</span>
                <div>
                  <h3 className="idea-title">{idea.title}</h3>
                  <p className="idea-desc">{idea.description}</p>
                </div>
              </div>
              <a href={idea.contact_url || "mailto:hello@example.com"} className="idea-link mono">
                Riff on it ↗
              </a>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
