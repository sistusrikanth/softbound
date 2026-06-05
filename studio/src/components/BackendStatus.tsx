import { useEffect, useState } from "react";
import { checkHealth } from "@/lib/api";

export function BackendStatus() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let cancelled = false;
    checkHealth(true).then((ok) => {
      if (!cancelled) setStatus(ok ? "online" : "offline");
    });
    const interval = setInterval(() => {
      checkHealth(true).then((ok) => {
        if (!cancelled) setStatus(ok ? "online" : "offline");
      });
    }, 60_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const label =
    status === "checking" ? "co-author: connecting…" : status === "online" ? "co-author: connected" : "co-author: offline (local mock)";

  return (
    <div
      className="backend-status"
      title={status === "offline" ? "Start softbound-backend on port 3000 for live LLM responses" : "Backend API connected"}
      style={{
        position: "fixed",
        left: 16,
        bottom: 16,
        zIndex: 9998,
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontFamily: "var(--font-ui)",
        fontSize: 11.5,
        color: "var(--fg-subtle)",
        background: "rgba(251,247,241,0.9)",
        border: "1px solid var(--hairline)",
        borderRadius: 999,
        padding: "6px 12px",
        boxShadow: "var(--shadow-1)",
      }}
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: status === "online" ? "var(--sage)" : status === "offline" ? "var(--danger)" : "var(--honey)",
        }}
      />
      {label}
    </div>
  );
}
