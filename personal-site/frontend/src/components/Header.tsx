import { Link, useLocation } from "react-router-dom";
import type { SiteConfig } from "../lib/types";
import "./Header.css";

const NAV = [
  { to: "/", label: "Index" },
  { to: "/writing", label: "Writing" },
  { to: "/systems", label: "Systems" },
  { to: "/experience", label: "Experience" },
  { to: "/photography", label: "Photography" },
  { to: "/projects", label: "Projects" },
];

interface Props {
  config: SiteConfig;
}

export default function Header({ config }: Props) {
  const { pathname } = useLocation();

  return (
    <header className="header">
      <div className="container header-inner">
        <Link to="/" className="header-logo">
          {config.name}
        </Link>

        <nav className="header-nav">
          {NAV.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={pathname === to || (to !== "/" && pathname.startsWith(to)) ? "active" : ""}
            >
              {label}
            </Link>
          ))}
        </nav>

        <div className="header-actions">
          <Link to="/admin" className="header-search">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            Admin
          </Link>
        </div>
      </div>
    </header>
  );
}
