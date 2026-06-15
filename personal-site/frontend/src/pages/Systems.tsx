import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Article } from "../lib/types";
import "./Systems.css";

const SYSTEM_DESIGNS = [
  {
    num: "01",
    label: "SYSTEM DESIGN",
    title: "A training cluster that survives node death",
    desc: "Fault-tolerant distributed training with automatic checkpoint recovery.",
    tags: ["distributed", "fault-tolerance"],
    flow: ["dataloader", "shard", "all-reduce", "ckpt"],
  },
  {
    num: "02",
    label: "SYSTEM DESIGN",
    title: "Designing a feature store",
    desc: "Online vs offline features, point-in-time correctness, and the serving path.",
    tags: ["data", "serving"],
    flow: ["ingest", "transform", "store", "serve"],
  },
  {
    num: "03",
    label: "SYSTEM DESIGN",
    title: "Vector search at 100M scale",
    desc: "ANN indexes, recall-latency tradeoffs, and when brute force wins.",
    tags: ["retrieval", "ann"],
    flow: ["embed", "index", "query", "rerank"],
  },
];

export default function SystemsPage() {
  const [codeArticles, setCodeArticles] = useState<Article[]>([]);

  useEffect(() => {
    api.getArticles("systems").then((arts) => {
      setCodeArticles(arts.slice(0, 3));
    });
  }, []);

  return (
    <div className="systems-page">
      <p className="section-label"><span>§</span> Systems Systems</p>
      <h1 className="page-title serif">Designed in the open.</h1>
      <p className="page-subtitle">
        The ML systems everyone leans on, drawn out from first principles — with the trade-offs left in, not airbrushed away.
      </p>

      <div className="systems-designs">
        {SYSTEM_DESIGNS.map((d) => (
          <div key={d.num} className="system-card card">
            <div className="system-card-header mono">
              <span>{d.num}</span>
              <span className="system-label">{d.label}</span>
            </div>
            <h2 className="system-title serif">{d.title}</h2>
            <p className="system-desc">{d.desc}</p>
            <div className="system-tags">
              {d.tags.map((t) => (
                <span key={t} className="tag">{t}</span>
              ))}
            </div>
            <div className="system-flow mono">
              {d.flow.map((step, i) => (
                <span key={step}>
                  {i > 0 && <span className="flow-arrow">→</span>}
                  <span className="flow-step">[{step}]</span>
                </span>
              ))}
            </div>
            <Link to="/writing" className="system-link mono">Open design ↗</Link>
          </div>
        ))}
      </div>

      <section className="code-section">
        <p className="section-label"><span>§</span> Code Code, broken down</p>
        <div className="code-grid">
          {codeArticles.length > 0 ? (
            codeArticles.map((a) => (
              <Link key={a.id} to={`/writing/${a.slug}`} className="code-card card">
                <div className="code-card-top mono">
                  <span>{"{ }"}</span>
                  <span className="code-filename">{a.slug.split("-")[0]}.md</span>
                  <span className="code-lang">MARKDOWN</span>
                </div>
                <p className="code-desc">{a.summary}</p>
                <div className="code-footer mono">
                  <span>{a.read_time_min} min</span>
                  <span>↗</span>
                </div>
              </Link>
            ))
          ) : (
            <p className="mono" style={{ color: "var(--text-dim)" }}>Add systems articles from the admin panel.</p>
          )}
        </div>
      </section>
    </div>
  );
}
