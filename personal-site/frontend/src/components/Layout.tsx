import { Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import Header from "./Header";
import Footer from "./Footer";
import { api } from "../lib/api";
import type { SiteConfig } from "../lib/types";

const DEFAULT_CONFIG: SiteConfig = {
  name: "srikanth sistu",
  tagline: "writing, systems & photography",
  location: "Lisbon",
  github: "",
  twitter: "",
  email: "",
  now_text: "",
};

export default function Layout() {
  const [config, setConfig] = useState<SiteConfig>(DEFAULT_CONFIG);

  useEffect(() => {
    api.getConfig().then(setConfig).catch(() => {});
  }, []);

  return (
    <>
      <Header config={config} />
      <main className="container" style={{ paddingTop: 48, paddingBottom: 48, minHeight: "70vh" }}>
        <Outlet context={config} />
      </main>
      <Footer config={config} />
    </>
  );
}
