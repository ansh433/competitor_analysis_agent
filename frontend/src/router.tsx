import {
  Outlet,
  createRootRouteWithContext,
  createRoute,
  createRouter,
  redirect,
} from "@tanstack/react-router";

import type { AuthContextValue } from "./auth/auth-context";
import { AppShell } from "./components/app-shell";
import { PagePlaceholder } from "./components/page-placeholder";
import { AuthPage } from "./pages/auth-page";

interface RouterContext {
  auth: AuthContextValue;
}

const rootRoute = createRootRouteWithContext<RouterContext>()({ component: Outlet });

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: () => <AuthPage mode="login" />,
});
const signupRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/signup",
  component: () => <AuthPage mode="signup" />,
});
const recoveryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/recover-password",
  component: () => <AuthPage mode="recover" />,
});
const resetRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/reset-password",
  component: () => <AuthPage mode="reset" />,
});

const protectedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: "protected",
  beforeLoad: ({ context }) => {
    if (!context.auth.currentUser) throw redirect({ to: "/login" });
  },
  component: AppShell,
});

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  beforeLoad: () => {
    throw redirect({ to: "/dashboard" });
  },
});

const pages = [
  ["/dashboard", "Decision desk", "Resume active research, review evidence coverage, and monitor open questions."],
  ["/research", "Start a research run", "Select a workspace and define the company question you need answered."],
  ["/workspaces", "Research workspaces", "Organize companies, comparisons, conversations, and saved evidence by mandate."],
  ["/workspaces/$workspaceId", "Workspace", "Review the companies and research artifacts held in this workspace."],
  ["/companies/$companyId", "Company dossier", "Inspect the canonical profile, timeline, competitors, and evidence ledger."],
  ["/comparisons/$comparisonId", "Company comparison", "Compare normalized capabilities, positioning, pricing, and evidence confidence."],
  ["/tracked-companies", "Tracked companies", "Keep priority companies ready for recurring research and monitoring."],
  ["/settings", "Account settings", "Manage your profile, password, model access, and research preferences."],
  ["/admin", "Administration", "Manage users, account access, and research quotas."],
] as const;

const protectedPages = pages.map(([path, title, description]) =>
  createRoute({
    getParentRoute: () => protectedRoute,
    path,
    component: () => <PagePlaceholder title={title} description={description} />,
  }),
);

const routeTree = rootRoute.addChildren([
  homeRoute,
  loginRoute,
  signupRoute,
  recoveryRoute,
  resetRoute,
  protectedRoute.addChildren(protectedPages),
]);

export const router = createRouter({ routeTree, context: { auth: undefined as never } });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

