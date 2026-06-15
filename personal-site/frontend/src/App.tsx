import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import PrivateGate from "./components/PrivateGate";
import IndexPage from "./pages/Index";
import WritingPage from "./pages/Writing";
import ArticlePage from "./pages/Article";
import SystemsPage from "./pages/Systems";
import PhotographyPage from "./pages/Photography";
import ProjectsPage from "./pages/Projects";
import ExperiencePage from "./pages/Experience";
import ExperienceProjectPage from "./pages/ExperienceProject";
import AdminPage from "./pages/Admin";
import DayTrackerPage from "./pages/DayTracker";
import IdentityPage from "./pages/Identity";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<IndexPage />} />
        <Route path="writing" element={<WritingPage />} />
        <Route path="writing/:slug" element={<ArticlePage />} />
        <Route path="systems" element={<SystemsPage />} />
        <Route path="photography" element={<PhotographyPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="experience" element={<ExperiencePage />} />
        <Route path="experience/:slug" element={<ExperienceProjectPage />} />
      </Route>
      <Route path="admin" element={<PrivateGate><AdminPage /></PrivateGate>} />
      <Route path="private/days" element={<PrivateGate><DayTrackerPage /></PrivateGate>} />
      <Route path="private/identity" element={<PrivateGate><IdentityPage /></PrivateGate>} />
    </Routes>
  );
}
