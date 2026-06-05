import { useCallback, useEffect, useState } from "react";
import type { LayoutMode, Tweaks } from "@/lib/types";

export const TWEAK_DEFAULTS: Tweaks = {
  layout: "studio",
  accent: "#C89B7B",
  grain: true,
  serifScale: 1,
};

export const ACCENTS: Record<string, [string, string]> = {
  clay: ["#C89B7B", "#A87A5B"],
  sage: ["#9DAE93", "#5A6B52"],
  sky: ["#9DB2BD", "#6E8794"],
  honey: ["#D8B06A", "#B4904A"],
  rose: ["#D9A59B", "#B97A6E"],
};

export function useTweaks(defaults: Tweaks = TWEAK_DEFAULTS) {
  const [values, setValues] = useState<Tweaks>(() => {
    try {
      const stored = localStorage.getItem("softbound:studio:tweaks");
      if (stored) return { ...defaults, ...JSON.parse(stored) };
    } catch {
      /* ignore */
    }
    return defaults;
  });

  const setTweak = useCallback(<K extends keyof Tweaks>(key: K, val: Tweaks[K]) => {
    setValues((prev) => {
      const next = { ...prev, [key]: val };
      localStorage.setItem("softbound:studio:tweaks", JSON.stringify(next));
      return next;
    });
  }, []);

  return [values, setTweak] as const;
}

export function TweaksPanel({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "`" && e.metaKey) setOpen((o) => !o);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        style={{
          position: "fixed",
          right: 16,
          bottom: 16,
          zIndex: 9999,
          width: 40,
          height: 40,
          borderRadius: "50%",
          background: "var(--ink)",
          color: "var(--paper)",
          border: "none",
          fontSize: 18,
          cursor: "pointer",
        }}
        title="Tweaks (⌘`)"
      >
        ⚙
      </button>
    );
  }

  return (
    <div
      style={{
        position: "fixed",
        right: 16,
        bottom: 16,
        zIndex: 9999,
        width: 280,
        maxHeight: "calc(100vh - 32px)",
        background: "rgba(250,249,247,.92)",
        backdropFilter: "blur(24px)",
        border: "1px solid var(--hairline)",
        borderRadius: 14,
        boxShadow: "var(--shadow-3)",
        overflow: "auto",
        padding: 14,
        font: '11.5px/1.4 ui-sans-serif, system-ui, sans-serif',
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <strong>Tweaks</strong>
        <button type="button" onClick={() => setOpen(false)} style={{ border: "none", background: "none", cursor: "pointer" }}>
          ✕
        </button>
      </div>
      {children}
    </div>
  );
}

export function TweakSection({ label }: { label: string }) {
  return (
    <div
      style={{
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        color: "var(--fg-subtle)",
        padding: "10px 0 6px",
      }}
    >
      {label}
    </div>
  );
}

export function TweakRadio({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: LayoutMode) => void;
}) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontWeight: 500, marginBottom: 6 }}>{label}</div>
      <div style={{ display: "flex", gap: 4, background: "var(--shell)", borderRadius: 8, padding: 2 }}>
        {options.map((o) => (
          <button
            key={o}
            type="button"
            onClick={() => onChange(o as LayoutMode)}
            style={{
              flex: 1,
              padding: "6px 8px",
              border: "none",
              borderRadius: 6,
              background: value === o ? "var(--cream)" : "transparent",
              fontWeight: 500,
              cursor: "pointer",
              boxShadow: value === o ? "var(--shadow-1)" : "none",
            }}
          >
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}

export function TweakToggle({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
      <span style={{ fontWeight: 500 }}>{label}</span>
      <button
        type="button"
        onClick={() => onChange(!value)}
        style={{
          width: 32,
          height: 18,
          borderRadius: 999,
          border: "none",
          background: value ? "#34c759" : "rgba(0,0,0,.15)",
          position: "relative",
          cursor: "pointer",
        }}
      >
        <i
          style={{
            position: "absolute",
            top: 2,
            left: value ? 16 : 2,
            width: 14,
            height: 14,
            borderRadius: "50%",
            background: "#fff",
            transition: "left 0.15s",
          }}
        />
      </button>
    </div>
  );
}

export function TweakColor({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontWeight: 500, marginBottom: 6 }}>{label}</div>
      <div style={{ display: "flex", gap: 6 }}>
        {options.map((o) => (
          <button
            key={o}
            type="button"
            onClick={() => onChange(o)}
            style={{
              flex: 1,
              height: 32,
              borderRadius: 6,
              border: value === o ? "2px solid var(--ink)" : "1px solid var(--hairline)",
              background: o,
              cursor: "pointer",
            }}
          />
        ))}
      </div>
    </div>
  );
}

export function TweakButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        width: "100%",
        height: 28,
        border: "none",
        borderRadius: 7,
        background: "rgba(0,0,0,.78)",
        color: "#fff",
        fontWeight: 500,
        cursor: "pointer",
        marginTop: 4,
      }}
    >
      {label}
    </button>
  );
}
