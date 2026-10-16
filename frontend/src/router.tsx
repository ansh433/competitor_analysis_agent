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
import { CompanyDetailPage } from "./pages/company-detail-page";
import { ComparisonPage } from "./pages/comparison-page";
import { ResearchStartPage } from "./pages/research-start-page";
import { TrackedCompaniesPage } from "./pages/tracked-companies-page";
import { WorkspaceDetailPage } from "./pages/workspace-detail-page";
import { WorkspacesPage } from "./pages/workspaces-page";

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

const researchRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: "/research",
  component: ResearchStartPage,
});
const workspacesRoute = createRoute({ getParentRoute: () => protectedRoute, path: "/workspaces", component: WorkspacesPage });
const workspaceDetailRoute = createRoute({ getParentRoute: () => protectedRoute, path: "/workspaces/$workspaceId", component: WorkspaceDetailPage });
const companyDetailRoute = createRoute({ getParentRoute: () => protectedRoute, path: "/companies/$companyId", component: CompanyDetailPage });
const trackedCompaniesRoute = createRoute({ getParentRoute: () => protectedRoute, path: "/tracked-companies", component: TrackedCompaniesPage });
const comparisonRoute = createRoute({ getParentRoute: () => protectedRoute, path: "/comparisons/$comparisonId", component: ComparisonPage });

const routeTree = rootRoute.addChildren([
  homeRoute,
  loginRoute,
  signupRoute,
  recoveryRoute,
  resetRoute,
  protectedRoute.addChildren([researchRoute, workspacesRoute, workspaceDetailRoute, companyDetailRoute, trackedCompaniesRoute, comparisonRoute, ...protectedPages]),
]);

export const router = createRouter({ routeTree, context: { auth: undefined as never } });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

