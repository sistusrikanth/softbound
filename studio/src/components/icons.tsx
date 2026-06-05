import type { ReactNode } from "react";

const PATHS: Record<string, ReactNode> = {
  back: <path d="M15 5 8 12l7 7" />,
  chevronLeft: <path d="M14.5 5 8 12l6.5 7" />,
  chevronRight: <path d="M9.5 5 16 12l-6.5 7" />,
  arrowRight: (
    <g>
      <path d="M5 12h13" />
      <path d="M13 6l6 6-6 6" />
    </g>
  ),
  close: <path d="M6 6l12 12M18 6 6 18" />,
  check: <path d="M5 13l4 4L19 7" />,
  plus: <path d="M12 5v14M5 12h14" />,
  settings: (
    <g>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.5 1.5 0 0 0 .3 1.65l.05.05a2 2 0 1 1-2.83 2.83l-.05-.05a1.5 1.5 0 0 0-1.65-.3 1.5 1.5 0 0 0-.9 1.37V21a2 2 0 0 1-4 0v-.1a1.5 1.5 0 0 0-1-1.37 1.5 1.5 0 0 0-1.65.3l-.05.05a2 2 0 1 1-2.83-2.83l.05-.05a1.5 1.5 0 0 0 .3-1.65 1.5 1.5 0 0 0-1.37-.9H3a2 2 0 0 1 0-4h.1a1.5 1.5 0 0 0 1.37-1 1.5 1.5 0 0 0-.3-1.65l-.05-.05a2 2 0 1 1 2.83-2.83l.05.05a1.5 1.5 0 0 0 1.65.3H9a1.5 1.5 0 0 0 .9-1.37V3a2 2 0 0 1 4 0v.1a1.5 1.5 0 0 0 .9 1.37 1.5 1.5 0 0 0 1.65-.3l.05-.05a2 2 0 1 1 2.83 2.83l-.05.05a1.5 1.5 0 0 0-.3 1.65V9a1.5 1.5 0 0 0 1.37.9H21a2 2 0 0 1 0 4h-.1a1.5 1.5 0 0 0-1.37.9Z" />
    </g>
  ),
  spark: (
    <g>
      <path d="M12 3c.4 3.2 1.8 4.6 5 5-3.2.4-4.6 1.8-5 5-.4-3.2-1.8-4.6-5-5 3.2-.4 4.6-1.8 5-5Z" />
      <path d="M18.5 13.5c.2 1.5.9 2.2 2.5 2.5-1.6.2-2.3.9-2.5 2.5-.2-1.6-.9-2.3-2.5-2.5 1.6-.3 2.3-1 2.5-2.5Z" />
    </g>
  ),
  pen: (
    <g>
      <path d="M14.5 5.5 18.5 9.5" />
      <path d="M5 19l1-4L16 5l3 3L9 18l-4 1Z" />
    </g>
  ),
  note: (
    <g>
      <path d="M5 5h14v9l-5 5H5Z" />
      <path d="M19 14h-5v5" />
    </g>
  ),
  book: (
    <g>
      <path d="M12 6c-1.8-1.4-4.6-1.6-7-1v13c2.4-.6 5.2-.4 7 1" />
      <path d="M12 6c1.8-1.4 4.6-1.6 7-1v13c-2.4-.6-5.2-.4-7 1" />
      <path d="M12 6v13" />
    </g>
  ),
  flow: (
    <g>
      <rect x="3.5" y="4.5" width="7" height="5" rx="1.5" />
      <rect x="13.5" y="14.5" width="7" height="5" rx="1.5" />
      <path d="M7 9.5v3.5a2 2 0 0 0 2 2h4.5" />
    </g>
  ),
  layers: (
    <g>
      <path d="M12 3.5 21 8l-9 4.5L3 8Z" />
      <path d="M3 12.5 12 17l9-4.5" />
      <path d="M3 16.5 12 21l9-4.5" />
    </g>
  ),
  versions: (
    <g>
      <circle cx="6" cy="12" r="2" />
      <circle cx="18" cy="6" r="2" />
      <circle cx="18" cy="18" r="2" />
      <path d="M8 12h4.5M12.5 12 16 7M12.5 12 16 17" />
    </g>
  ),
  send: <path d="M5 12 19 5l-4 14-3-6-7-1Z" />,
  sun: (
    <g>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M5 5l1.4 1.4M17.6 17.6 19 19M3 12h2M19 12h2M5 19l1.4-1.4M17.6 6.4 19 5" />
    </g>
  ),
  moon: <path d="M20 13.5A8.5 8.5 0 1 1 10 3.5a6.5 6.5 0 0 0 10 10Z" />,
  play: <path d="M8 5v14l11-7Z" />,
  hand: (
    <g>
      <path d="M9 11V5.5a1.5 1.5 0 0 1 3 0V11" />
      <path d="M12 10.5V4.5a1.5 1.5 0 0 1 3 0V11" />
      <path d="M15 11V6a1.5 1.5 0 0 1 3 0v7a6 6 0 0 1-6 6h-1.2a4 4 0 0 1-3.1-1.5L6 16c-1.2-1.4 1-3.3 2.3-2L9 15V5.8a1.5 1.5 0 0 1 3 0" />
    </g>
  ),
  feather: (
    <g>
      <path d="M19 5c-4 0-9 2-11.5 7.5L5 19" />
      <path d="M19 5c.5 4-1 9-6.5 11l-5 1" />
      <path d="M9 13h5" />
    </g>
  ),
  sparkSmall: (
    <path d="M12 4c.4 3.2 1.4 4.2 4.5 4.5-3.1.4-4.1 1.3-4.5 4.5-.4-3.2-1.4-4.1-4.5-4.5C10.6 8.2 11.6 7.2 12 4Z" />
  ),
  trash: (
    <g>
      <path d="M5 7h14" />
      <path d="M9 7V5h6v2" />
      <path d="M7 7l1 12h8l1-12" />
    </g>
  ),
};

export function Icon({
  name,
  size = 18,
  stroke = 1.5,
  style,
  className,
}: {
  name: string;
  size?: number;
  stroke?: number;
  style?: React.CSSProperties;
  className?: string;
}) {
  const inner = PATHS[name];
  if (!inner) return null;
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={style}
      className={className}
      aria-hidden="true"
    >
      {inner}
    </svg>
  );
}

export function BookMark({ size = 26 }: { size?: number }) {
  return (
    <svg viewBox="0 0 120 120" width={size} height={size} aria-hidden="true">
      <g fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
        <rect x="32" y="38" width="56" height="14" rx="2" transform="translate(-.78 1.05) rotate(-1)" />
        <line x1="41.88" y1="38.32" x2="42.12" y2="52.31" />
        <rect x="53" y="29" width="14" height="72" rx="2" transform="translate(-7.05 122.69) rotate(-88)" />
        <line x1="34.26" y1="57.1" x2="33.77" y2="71.09" />
        <rect x="18" y="80" width="84" height="14" rx="2" transform="translate(-4.47 3.26) rotate(-3)" />
        <line x1="27.68" y1="81.68" x2="28.41" y2="95.67" />
      </g>
    </svg>
  );
}
