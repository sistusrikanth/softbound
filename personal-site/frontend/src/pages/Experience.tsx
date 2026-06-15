import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Experience } from "../lib/types";
import "./Experience.css";

export default function ExperiencePage() {
  const [data, setData] = useState<Experience | null>(null);

  useEffect(() => {
    api.getExperience().then(setData).catch(() => {});
  }, []);

  if (!data) {
    return <p className="mono" style={{ color: "var(--text-dim)" }}>Loading…</p>;
  }

  return (
    <div className="experience-page">
      <p className="section-label"><span>§</span> Experience Work</p>
      <h1 className="page-title serif">Where I've built.</h1>
      <p className="page-subtitle">
        Education, roles, and ML systems work — with deeper technical write-ups for selected projects.
      </p>

      <section className="experience-section">
        <h2 className="experience-section-title mono">Education</h2>
        <div className="timeline-list">
          {data.education.map((edu) => (
            <article key={edu.id} className="timeline-item card">
              <div className="timeline-meta mono">
                {edu.start_year}{edu.end_year ? ` – ${edu.end_year}` : ""}
              </div>
              <h3 className="timeline-title">{edu.institution}</h3>
              <p className="timeline-subtitle">
                {edu.degree}{edu.field ? `, ${edu.field}` : ""}
              </p>
              {edu.description && <p className="timeline-desc">{edu.description}</p>}
            </article>
          ))}
        </div>
      </section>

      <section className="experience-section">
        <h2 className="experience-section-title mono">Work history</h2>
        <div className="timeline-list">
          {data.work.map((job) => (
            <article key={job.id} className="timeline-item card">
              <div className="timeline-meta mono">
                {job.start_date}{job.end_date ? ` – ${job.end_date}` : ""}
                {job.location ? ` · ${job.location}` : ""}
              </div>
              <h3 className="timeline-title">{job.role}</h3>
              <p className="timeline-subtitle">{job.company}</p>
              {job.description && <p className="timeline-desc">{job.description}</p>}
            </article>
          ))}
        </div>
      </section>

      <section className="experience-section">
        <h2 className="experience-section-title mono">Project overview</h2>
        <p className="experience-section-intro">
          High-level summaries of ML systems I've shipped. Select a project for component-level technical detail.
        </p>
        <div className="experience-project-grid">
          {data.projects.map((project) => (
            <Link key={project.id} to={`/experience/${project.slug}`} className="experience-project-card card">
              <p className="experience-project-context mono">{project.role_context}</p>
              <h3 className="experience-project-title">{project.title}</h3>
              <p className="experience-project-summary">{project.summary}</p>
              <span className="experience-project-link mono">View technical detail →</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
