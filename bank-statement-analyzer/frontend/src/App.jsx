import { Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import CalendarPlanner from "./pages/CalendarPlanner.jsx";
import UploadPage from "./pages/UploadPage.jsx";

export default function App() {
  const { pathname } = useLocation();
  const page = pathname === "/upload"
    ? { title: "Import data", detail: "Bring your financial picture into focus." }
    : pathname === "/planner"
      ? { title: "Calendar planner", detail: "Plan ahead for the days that matter." }
      : { title: "Financial overview", detail: "A clearer view of where your money is going." };

  return (
    <div className="app-shell min-h-screen text-neutral-900">
      <Navbar />
      <div className="app-main">
        <main className="page-content">
          <header className="page-heading">
            <div>
              <p className="eyebrow">YOUR FINANCIAL WORKSPACE</p>
              <h1>{page.title}</h1>
              <p className="page-subtitle">{page.detail}</p>
            </div>
            <div className="workspace-badge"><span /> Private workspace</div>
          </header>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/planner" element={<CalendarPlanner />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
