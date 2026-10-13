import { Link, Outlet, useNavigate } from "@tanstack/react-router";
import {
  BarChart3,
  Building2,
  Compass,
  FileSearch,
  LogOut,
  Settings,
  ShieldCheck,
  Telescope,
} from "lucide-react";

import { useAuth } from "../auth/auth-context";

const mainLinks = [
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { to: "/research", label: "New research", icon: Telescope },
  { to: "/workspaces", label: "Workspaces", icon: Building2 },
  { to: "/tracked-companies", label: "Tracked companies", icon: FileSearch },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export function AppShell(): React.JSX.Element {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout(): void {
    logout();
    void navigate({ to: "/login" });
  }

  return (
    <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)]">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-[var(--line)] bg-[var(--navy)] text-white lg:flex lg:flex-col">
        <div className="flex h-20 items-center gap-3 border-b border-white/10 px-6">
          <span className="grid size-10 place-items-center bg-[var(--signal)] text-[var(--navy)]">
            <Compass aria-hidden="true" size={22} />
          </span>
          <div>
            <p className="font-display text-xl leading-none">Compass</p>
            <p className="mt-1 text-xs text-teal-100/70">Company intelligence</p>
          </div>
        </div>
        <nav aria-label="Primary" className="flex-1 space-y-1 p-4">
          {mainLinks.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className="flex min-h-12 items-center gap-3 px-3 text-sm text-teal-50/75 transition-colors hover:bg-white/8 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--signal)]"
              activeProps={{ className: "bg-white/12 text-white" }}
            >
              <Icon aria-hidden="true" size={18} />
              {label}
            </Link>
          ))}
          {currentUser?.is_superuser ? (
            <Link
              to="/admin"
              className="flex min-h-12 items-center gap-3 px-3 text-sm text-teal-50/75 hover:bg-white/8 hover:text-white"
              activeProps={{ className: "bg-white/12 text-white" }}
            >
              <ShieldCheck aria-hidden="true" size={18} />
              Administration
            </Link>
          ) : null}
        </nav>
        <div className="border-t border-white/10 p-4">
          <p className="truncate px-3 text-sm font-medium">{currentUser?.full_name ?? "Research analyst"}</p>
          <p className="truncate px-3 pb-3 text-xs text-teal-100/60">{currentUser?.email}</p>
          <button
            type="button"
            onClick={handleLogout}
            className="flex min-h-11 w-full items-center gap-3 px-3 text-sm text-teal-50/75 hover:bg-white/8 hover:text-white"
          >
            <LogOut aria-hidden="true" size={17} />
            Sign out
          </button>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-[var(--line)] bg-[var(--paper)]/95 px-5 lg:px-10">
          <Link to="/dashboard" className="flex items-center gap-2 font-display text-lg lg:hidden">
            <Compass aria-hidden="true" size={20} /> Compass
          </Link>
          <div className="hidden items-center gap-2 text-sm text-[var(--muted)] lg:flex">
            <Telescope aria-hidden="true" size={17} /> Evidence before assertion
          </div>
          <Link
            to="/research"
            className="inline-flex min-h-11 items-center bg-[var(--navy)] px-4 text-sm font-semibold text-white hover:bg-[var(--navy-light)]"
          >
            Start research
          </Link>
        </header>
        <main className="px-5 py-8 lg:px-10 lg:py-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

