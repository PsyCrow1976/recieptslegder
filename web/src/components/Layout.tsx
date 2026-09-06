import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../auth";

const items = [
  { to: "/", label: "Home", end: true },
  { to: "/people", label: "People" },
  { to: "/platforms", label: "Platforms" },
  { to: "/accounts", label: "Accounts" },
  { to: "/entries", label: "Entries" },
  { to: "/vendors", label: "Vendors" },
  { to: "/categories", label: "Categories" },
];

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive ? "bg-brand-600 text-white" : "text-stone-600 hover:bg-white"
  }`;

export default function Layout({ children }: { children: React.ReactNode }) {
  const { logout } = useAuth();

  return (
    <div className="min-h-screen md:flex">
      <aside className="border-b border-stone-200 bg-[#efe8d9] md:flex md:w-60 md:flex-col md:border-b-0 md:border-r">
        <div className="px-4 py-5">
          <Link to="/" className="serif text-xl text-brand-700">
            Household Ledger
          </Link>
          <p className="mt-1 text-xs text-stone-500">Banks, investments, receipts</p>
        </div>
        <nav className="flex flex-wrap gap-1 px-3 pb-3 md:flex-1 md:flex-col">
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
              {item.label}
            </NavLink>
          ))}
          <button onClick={logout} className="mt-auto rounded-lg px-3 py-2 text-left text-sm font-medium text-stone-600 hover:bg-white">
            Log out
          </button>
        </nav>
      </aside>
      <main className="flex-1 px-4 py-6 md:px-8">{children}</main>
    </div>
  );
}
