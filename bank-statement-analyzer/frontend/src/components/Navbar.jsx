import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", icon: "grid", end: true },
  { to: "/upload", label: "Upload", icon: "upload" },
  { to: "/planner", label: "Calendar Planner", icon: "calendar" },
];

function NavIcon({ name }) {
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    upload: <><path d="M12 16V4" /><path d="m7 9 5-5 5 5" /><path d="M4 16v4h16v-4" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 11h18" /><path d="M8 15h.01M12 15h.01M16 15h.01" /></>,
  };
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

export default function Navbar() {
  return (
    <aside className="sidebar">
      <div className="brand-lockup">
        <div className="brand-mark"><span /></div>
        <div className="brand-copy">
          <span className="brand-name">Ledgerly</span>
          <span className="brand-caption">FINANCIAL INTELLIGENCE</span>
        </div>
      </div>
      <div className="sidebar-label">WORKSPACE</div>
      <nav className="sidebar-nav" aria-label="Main navigation">
        {links.map(({ to, label, icon, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
            <NavIcon name={icon} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="privacy-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" /><path d="m9 12 2 2 4-4" /></svg></div>
        <div><strong>Your data stays yours</strong><span>Private by design</span></div>
      </div>
    </aside>
  );
}
