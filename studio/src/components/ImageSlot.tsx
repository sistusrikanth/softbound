import { useCallback, useEffect, useRef, useState } from "react";

const SLOT_KEY = "softbound:image-slots";

type SlotValue = { u: string };

function loadSlots(): Record<string, SlotValue> {
  try {
    return JSON.parse(localStorage.getItem(SLOT_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

function saveSlots(slots: Record<string, SlotValue>) {
  localStorage.setItem(SLOT_KEY, JSON.stringify(slots));
}

async function fileToDataUrl(file: File, maxDim = 1200): Promise<string> {
  const bitmap = await createImageBitmap(file);
  try {
    const scale = Math.min(1, maxDim / Math.max(bitmap.width, bitmap.height));
    const w = Math.max(1, Math.round(bitmap.width * scale));
    const h = Math.max(1, Math.round(bitmap.height * scale));
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    canvas.getContext("2d")!.drawImage(bitmap, 0, 0, w, h);
    return canvas.toDataURL("image/webp", 0.85);
  } finally {
    bitmap.close?.();
  }
}

export function ImageSlot({
  id,
  shape = "rounded",
  radius = 12,
  placeholder = "Drop an image",
  className,
}: {
  id: string;
  shape?: "rect" | "rounded" | "circle" | "pill";
  radius?: number;
  placeholder?: string;
  className?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState<string | null>(() => loadSlots()[id]?.u ?? null);
  const [over, setOver] = useState(false);

  const borderRadius =
    shape === "circle" ? "50%" : shape === "pill" ? "9999px" : shape === "rounded" ? `${radius}px` : "0";

  const ingest = useCallback(
    async (file: File) => {
      if (!file.type.startsWith("image/")) return;
      const dataUrl = await fileToDataUrl(file);
      setUrl(dataUrl);
      const slots = loadSlots();
      slots[id] = { u: dataUrl };
      saveSlots(slots);
    },
    [id],
  );

  useEffect(() => {
    const stored = loadSlots()[id]?.u;
    if (stored) setUrl(stored);
  }, [id]);

  return (
    <div
      className={`image-slot ${className ?? ""}`}
      style={{
        position: "relative",
        borderRadius,
        overflow: "hidden",
        background: "rgba(0,0,0,0.04)",
        border: over ? "2px solid var(--accent)" : "1.5px dashed var(--border)",
        cursor: "pointer",
      }}
      onClick={() => inputRef.current?.click()}
      onDragEnter={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragOver={(e) => e.preventDefault()}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f) ingest(f);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/avif"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) ingest(f);
          e.target.value = "";
        }}
      />
      {url ? (
        <img src={url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
      ) : (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 6,
            padding: 12,
            fontSize: 12,
            color: "var(--fg-subtle)",
            textAlign: "center",
          }}
        >
          <span style={{ fontWeight: 500 }}>{placeholder}</span>
          <span style={{ fontSize: 11 }}>drop or click</span>
        </div>
      )}
    </div>
  );
}
