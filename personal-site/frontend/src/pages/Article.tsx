import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import ArticleContent from "../components/ArticleContent";
import { api, categoryLabel, formatDate } from "../lib/api";
import type { Article } from "../lib/types";
import "./Article.css";

export default function ArticlePage() {
  const { slug } = useParams<{ slug: string }>();
  const [article, setArticle] = useState<Article | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!slug) return;
    api.getArticle(slug).then(setArticle).catch(() => setError("Article not found"));
  }, [slug]);

  if (error) {
    return (
      <div>
        <p>{error}</p>
        <Link to="/writing">← Back to writing</Link>
      </div>
    );
  }

  if (!article) return <p className="mono" style={{ color: "var(--text-dim)" }}>Loading…</p>;

  return (
    <article className="article-page">
      <Link to="/writing" className="article-back mono">← Writing</Link>
      <div className="article-meta-top">
        <span className={`article-type mono type-${article.category}`}>{categoryLabel(article.category)}</span>
        <span className="mono article-meta-item">{formatDate(article.created_at)}</span>
        <span className="mono article-meta-item">{article.read_time_min} min read</span>
      </div>
      <h1 className="article-title serif">{article.title}</h1>
      <p className="article-summary">{article.summary}</p>
      <div className="article-content">
        <ArticleContent content={article.content} />
      </div>
    </article>
  );
}
