import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ArticleContent from "../components/ArticleContent";
import { api } from "../lib/api";
import type { ExperienceProjectDetail } from "../lib/types";
import "./Experience.css";

export default function ExperienceProjectPage() {
  const { slug } = useParams<{ slug: string }>();
  const [project, setProject] = useState<ExperienceProjectDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!slug) return;
    api.getExperienceProject(slug).then(setProject).catch(() => setError("Project not found"));
  }, [slug]);

  if (error) {
    return (
      <div>
        <p>{error}</p>
        <Link to="/experience">← Back to experience</Link>
      </div>
    );
  }

  if (!project) {
    return <p className="mono" style={{ color: "var(--text-dim)" }}>Loading…</p>;
  }

  return (
    <article className="experience-detail-page">
      <Link to="/experience" className="experience-back mono">← Experience</Link>
      <p className="experience-detail-context mono">{project.role_context}</p>
      <h1 className="page-title serif">{project.title}</h1>
      <p className="experience-detail-summary">{project.summary}</p>

      <section className="experience-components">
        <h2 className="experience-section-title mono">ML components</h2>
        <div className="component-grid">
          {project.ml_components.map((component) => (
            <div key={component.name} className="component-card card">
              <h3 className="component-name">{component.name}</h3>
              {component.description && (
                <p className="component-desc">{component.description}</p>
              )}
              {component.technical_aspects.length > 0 && (
                <ul className="component-aspects">
                  {component.technical_aspects.map((aspect) => (
                    <li key={aspect} className="mono">{aspect}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </section>

      {project.technical_detail && (
        <section className="experience-detail-body">
          <h2 className="experience-section-title mono">Technical deep dive</h2>
          <ArticleContent content={project.technical_detail} />
        </section>
      )}
    </article>
  );
}
