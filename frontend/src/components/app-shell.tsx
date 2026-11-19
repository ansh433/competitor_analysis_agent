import * as Dialog from "@radix-ui/react-dialog";
import { Link, Outlet, useNavigate } from "@tanstack/react-router";
import {
  BarChart3,
  Building2,
  Compass,
  FileSearch,
  LogOut,
  Menu,
  Settings,
  ShieldCheck,
  Telescope,
  X,
} from "lucide-react";
import { useState } from "react";

import { useAuth } from "../auth/auth-context";

const mainLinks = [
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { to: "/research", label: "New research", icon: Telescope },
  { to: "/workspaces", label: "Workspaces", icon: Building2 },
  { to: "/tracked-companies", label: "Tracked companies", icon: FileSearch },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

interface NavigationListProps {
  isAdmin: boolean;
  onNavigate?: () => void;
}

function NavigationList({
  isAdmin,
  onNavigate,
}: NavigationListProps): React.JSX.Element {
  return (
    <nav aria-label="Primary" className="flex-1 space-y-1 p-3">
      {mainLinks.map(({ to, label, icon: Icon }) => (
        <Link
          key={to}
          to={to}
          onClick={onNavigate}
          className="flex min-h-11 items-center gap-3 rounded-[3px] px-3 text-sm text-emerald-50/75 hover:bg-white/8 hover:text-white focus-visible:outline-brass"
          activeProps={{ className: "bg-pine-soft text-white" }}
        >
          <Icon aria-hidden="true" size={17} strokeWidth={1.8} />
          {label}
        </Link>
      ))}
      {isAdmin ? (
        <Link
          to="/admin"
          onClick={onNavigate}
          className="flex min-h-11 items-center gap-3 rounded-[3px] px-3 text-sm text-emerald-50/75 hover:bg-white/8 hover:text-white"
          activeProps={{ className: "bg-pine-soft text-white" }}
        >
          <ShieldCheck aria-hidden="true" size={17} strokeWidth={1.8} />
          Administration
        </Link>
      ) : null}
    </nav>
  );
}

function Brand(): React.JSX.Element {
  return (
    <Link to="/dashboard" className="flex items-center gap-3">
      <span className="grid size-9 place-items-center rounded-[3px] bg-brass text-pine">
        <Compass aria-hidden="true" size={20} />
      </span>
      <span>
        <strong className="block font-serif text-lg font-medium leading-none">
          Compass
        </strong>
        <span className="mt-1 block text-[0.68rem] text-emerald-50/60">
          Company intelligence
        </span>
      </span>
    </Link>
  );
}

export function AppShell(): React.JSX.Element {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  function handleLogout(): void {
    logout();
    setIsDrawerOpen(false);
    void navigate({ to: "/login" });
  }

  const userFooter = (
    <div className="border-t border-white/10 p-3">
      <p className="truncate px-3 pt-1 text-sm font-medium">
        {currentUser?.full_name ?? "Research analyst"}
      </p>
      <p className="truncate px-3 pb-2 text-xs text-emerald-50/55">
        {currentUser?.email}
      </p>
      <button
        type="button"
        onClick={handleLogout}
        className="flex min-h-11 w-full items-center gap-3 rounded-[3px] px-3 text-sm text-emerald-50/75 hover:bg-white/8 hover:text-white"
      >
        <LogOut aria-hidden="true" size={17} />
        Sign out
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-60 border-r border-white/8 bg-pine text-white lg:flex lg:flex-col">
        <div className="flex h-16 items-center border-b border-white/10 px-5">
          <Brand />
        </div>
        <NavigationList isAdmin={currentUser?.is_superuser ?? false} />
        {userFooter}
      </aside>

      <div className="lg:pl-60">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-hairline bg-canvas/95 px-4 backdrop-blur-sm sm:px-8 lg:justify-end">
          <div className="flex items-center gap-3 lg:hidden">
            <Dialog.Root open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
              <Dialog.Trigger asChild>
                <button
                  type="button"
                  aria-label="Open navigation"
                  className="grid size-11 place-items-center rounded-xl border border-hairline bg-surface shadow-quiet"
                >
                  <Menu aria-hidden="true" size={20} />
                </button>
              </Dialog.Trigger>
              <Dialog.Portal>
                <Dialog.Overlay className="drawer-overlay" />
                <Dialog.Content className="drawer-content flex flex-col">
                  <Dialog.Title className="sr-only">Navigation</Dialog.Title>
                  <Dialog.Description className="sr-only">
                    Navigate between your research workspaces.
                  </Dialog.Description>
                  <div className="flex h-16 items-center justify-between border-b border-white/10 px-5">
                    <Brand />
                    <Dialog.Close
                      aria-label="Close navigation"
                      className="grid size-11 place-items-center rounded-[3px] text-emerald-50/80 hover:bg-white/8 hover:text-white"
                    >
                      <X aria-hidden="true" size={20} />
                    </Dialog.Close>
                  </div>
                  <NavigationList
                    isAdmin={currentUser?.is_superuser ?? false}
                    onNavigate={() => setIsDrawerOpen(false)}
                  />
                  {userFooter}
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>
          </div>
          <Link to="/research" className="button-primary">
            <Telescope aria-hidden="true" size={16} />
            <span className="hidden sm:inline">New research</span>
            <span className="sm:hidden">Research</span>
          </Link>
        </header>
        <main className="px-4 py-7 sm:px-8 sm:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
