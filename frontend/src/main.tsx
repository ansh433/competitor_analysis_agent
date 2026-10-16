import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { AuthProvider, useAuth } from "./auth/auth-context";
import { router } from "./router";
import "./styles.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

function ApplicationRouter(): React.JSX.Element {
  const auth = useAuth();
  if (auth.isLoading) {
    return (
      <main className="grid min-h-screen place-items-center bg-[var(--paper)]">
        Loading workspace…
      </main>
    );
  }
  return <RouterProvider router={router} context={{ auth }} />;
}

const root = document.getElementById("root");
if (!root) throw new Error("Missing root element");
createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ApplicationRouter />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
);
