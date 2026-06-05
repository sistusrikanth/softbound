import { useCallback, useEffect, useState } from "react";
import type { Route, World } from "@/lib/types";
import { blankWorld, loadLibrary, saveLibrary } from "@/lib/storage";
import { WorldsHome } from "./components/WorldsHome";
import { WorldEditor } from "./components/WorldEditor";
import { BackendStatus } from "./components/BackendStatus";
import { ACCENTS, TWEAK_DEFAULTS, useTweaks } from "./components/TweaksPanel";

export default function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [worlds, setWorlds] = useState<World[]>(loadLibrary);
  const [route, setRoute] = useState<Route>({ name: "home" });

  const [isMobile, setIsMobile] = useState(
    () => typeof window !== "undefined" && window.matchMedia("(max-width: 760px)").matches,
  );

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 760px)");
    const on = () => setIsMobile(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);

  useEffect(() => {
    const deep = Object.values(ACCENTS).find((p) => p[0] === t.accent);
    document.documentElement.style.setProperty("--accent", t.accent);
    document.documentElement.style.setProperty("--accent-deep", deep ? deep[1] : t.accent);
    document.documentElement.style.setProperty("--focus-ring", t.accent + "55");
  }, [t.accent]);

  useEffect(() => {
    saveLibrary(worlds);
  }, [worlds]);

  const persistWorld = useCallback((id: string, patch: Partial<World>) => {
    setWorlds((ws) => ws.map((w) => (w.id === id ? { ...w, ...patch, id, updatedAt: Date.now() } : w)));
  }, []);

  const openWorld = (id: string) => setRoute({ name: "world", worldId: id });
  const newWorld = () => {
    const w = blankWorld();
    setWorlds((ws) => [w, ...ws]);
    setRoute({ name: "world", worldId: w.id });
  };
  const deleteWorld = (id: string) => {
    setWorlds((ws) => ws.filter((w) => w.id !== id));
    if (route.name === "world" && route.worldId === id) setRoute({ name: "home" });
  };
  const goHome = () => setRoute({ name: "home" });

  const activeWorld = route.name === "world" ? worlds.find((w) => w.id === route.worldId) : null;

  if (route.name === "home" || !activeWorld) {
    return (
      <div className={"app home-app" + (t.grain ? " grain" : "")} style={{ fontSize: 16 }}>
        <WorldsHome worlds={worlds} onOpen={openWorld} onNew={newWorld} onDelete={deleteWorld} />
        <BackendStatus />
      </div>
    );
  }

  return (
    <>
      <WorldEditor
      key={activeWorld.id}
      world={activeWorld}
      onPersist={persistWorld}
      onHome={goHome}
      isMobile={isMobile}
      t={t}
      setTweak={setTweak}
    />
      <BackendStatus />
    </>
  );
}
