import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import type { PhotoLink } from "../lib/types";
import "./Photography.css";

const CATEGORIES = ["all", "street", "landscape", "architecture", "portrait"] as const;

export default function PhotographyPage() {
  const [photos, setPhotos] = useState<PhotoLink[]>([]);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    api.getPhotos().then(setPhotos);
  }, []);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: photos.length };
    for (const cat of ["street", "landscape", "architecture", "portrait"]) {
      c[cat] = photos.filter((p) => p.category === cat).length;
    }
    return c;
  }, [photos]);

  const filtered = filter === "all" ? photos : photos.filter((p) => p.category === filter);

  return (
    <div className="photography-page">
      <p className="section-label"><span>§</span> Photography Photography</p>
      <h1 className="page-title serif">Light, on the side.</h1>
      <p className="page-subtitle">
        A working portfolio shot between systems and sentences. Film when there's time, digital when there isn't.
      </p>

      <div className="filter-bar">
        {CATEGORIES.map((cat) => (
          <button key={cat} className={filter === cat ? "active" : ""} onClick={() => setFilter(cat)}>
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
            <span>{counts[cat] || 0}</span>
          </button>
        ))}
      </div>

      <div className="photo-grid">
        {filtered.map((photo, i) => (
          <a
            key={photo.id}
            href={photo.instagram_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`photo-frame photo-aspect-${i % 3}`}
          >
            <div className="photo-placeholder">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="3" />
                <path d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              </svg>
              {photo.title && <span className="photo-title mono">{photo.title}</span>}
              <span className="photo-link-hint mono">View on Instagram ↗</span>
            </div>
          </a>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="mono photo-empty">No photos yet — add Instagram links from the admin panel.</p>
      )}
    </div>
  );
}
