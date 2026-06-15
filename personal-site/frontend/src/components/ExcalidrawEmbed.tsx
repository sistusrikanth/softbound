import { useEffect, useState, type ComponentType } from "react";
import "@excalidraw/excalidraw/index.css";
import "./ExcalidrawEmbed.css";

type ExcalidrawData = {
  type?: string;
  elements?: unknown[];
  appState?: Record<string, unknown>;
  files?: Record<string, unknown>;
};

export default function ExcalidrawEmbed({ src }: { src: string }) {
  const [data, setData] = useState<ExcalidrawData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(src)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load diagram");
        return res.json();
      })
      .then(setData)
      .catch(() => setError("Could not load Excalidraw diagram"));
  }, [src]);

  if (error) {
    return (
      <div className="excalidraw-embed excalidraw-embed-error">
        <p>{error}</p>
        <a href={src} download>Download .excalidraw file</a>
      </div>
    );
  }

  if (!data) {
    return <div className="excalidraw-embed excalidraw-embed-loading mono">Loading diagram…</div>;
  }

  return (
    <div className="excalidraw-embed">
      <div className="excalidraw-embed-header mono">
        <span>Excalidraw diagram</span>
        <a href={src} download>Download</a>
      </div>
      <ExcalidrawCanvas data={data} />
    </div>
  );
}

function ExcalidrawCanvas({ data }: { data: ExcalidrawData }) {
  const [Excalidraw, setExcalidraw] = useState<ComponentType<Record<string, unknown>> | null>(null);

  useEffect(() => {
    import("@excalidraw/excalidraw").then((mod) => {
      setExcalidraw(() => mod.Excalidraw as ComponentType<Record<string, unknown>>);
    });
  }, []);

  if (!Excalidraw) {
    return <div className="excalidraw-embed-loading mono">Loading viewer…</div>;
  }

  return (
    <div className="excalidraw-embed-canvas">
      <Excalidraw
        initialData={{
          elements: data.elements || [],
          appState: { viewBackgroundColor: "#f6f5f2", ...(data.appState || {}) },
          files: data.files || {},
        }}
        viewModeEnabled
        zenModeEnabled
        gridModeEnabled={false}
        UIOptions={{ canvasActions: { toggleTheme: false } }}
      />
    </div>
  );
}
