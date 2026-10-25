import { NavLink, Link } from "react-router-dom";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "../context/ThemeContext";

export function Layout({ children }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <div className="header-left">
            <Link to="/" className="brand-block brand-link" aria-label="Wind Forecast Monitor Home">
              <svg
                width="32"
                height="32"
                viewBox="0 0 32 32"
                aria-hidden="true"
                className="brand-logo-svg"
              >
                <rect
                  width="32"
                  height="32"
                  rx="7"
                  fill="var(--bg-subtle)"
                  stroke="var(--border-subtle)"
                  strokeWidth="1"
                />
                <path
                  d="M6 12 C10 7, 14 7, 17 11 S24 15, 26 9"
                  fill="none"
                  stroke="var(--text-main)"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
                <path
                  d="M6 22 C10 17, 14 17, 17 21 S24 25, 26 19"
                  fill="none"
                  stroke="var(--color-forecast)"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
              <div>
                <div className="brand-name">Wind Forecast Monitor</div>
                <div className="brand-desc">GB day-ahead · national wind</div>
              </div>
            </Link>

            <nav aria-label="Views" className="nav-links">
              <NavLink
                to="/forecast"
                className={({ isActive }) =>
                  `nav-tab ${isActive ? "nav-tab-active" : ""}`
                }
              >
                Decision-time forecast
              </NavLink>
              <NavLink
                to="/accuracy"
                className={({ isActive }) =>
                  `nav-tab ${isActive ? "nav-tab-active" : ""}`
                }
              >
                Forecast accuracy
              </NavLink>
            </nav>
          </div>

          <div className="header-right-actions">
            <button
              type="button"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
              title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
            >
              {theme === "light" ? (
                <>
                  <Moon size={15} />
                  <span>Dark</span>
                </>
              ) : (
                <>
                  <Sun size={15} />
                  <span>Light</span>
                </>
              )}
            </button>

            <div className="header-badge">Live Elexon BMRS · Jan 2026</div>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="main-content">{children}</div>
      </main>

      <footer className="app-footer">
        <div className="footer-inner">
          Source: Elexon BMRS, FUELHH (actual) and WINDFOR (forecast), national
          wind generation for Great Britain. Used under the BMRS Data Licence
          terms. Data window: delivery days 2 Jan – 1 Feb 2026.
        </div>
      </footer>
    </div>
  );
}
