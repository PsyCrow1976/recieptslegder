import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../auth";

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive ? "bg-brand-600 text-white" : "text-stone-600 hover:bg-stone-100"
  }`;

export default function Layout({ children }: { children: React.ReactNode }) {
  const { logout } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Link to="/" className="text-xl font-bold text-brand-700">
              Receipts Ledger
            </Link>
            <p className="text-sm text-stone-500">Scan, tag, and calendar Danish receipts</p>
          </div>
          <nav className="flex flex-wrap gap-2">
            <NavLink to="/" end className={navClass}>
              Dashboard
            </NavLink>
            <NavLink to="/upload" className={navClass}>
              Upload
            </NavLink>
            <NavLink to="/receipts" className={navClass}>
              Receipts
            </NavLink>
            <NavLink to="/calendar" className={navClass}>
              Calendar
            </NavLink>
            <NavLink to="/tags" className={navClass}>
              Tags
            </NavLink>
            <button
              onClick={logout}
              className="rounded-lg px-3 py-2 text-sm font-medium text-stone-600 hover:bg-stone-100"
            >
              Logout
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
