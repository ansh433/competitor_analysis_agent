import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { apiRequest, clearStoredToken, getStoredToken, storeToken } from "../api/client";

export interface AuthenticatedUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
}

interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface AuthContextValue {
  currentUser: AuthenticatedUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const [currentUser, setCurrentUser] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function refreshUser(): Promise<void> {
    if (!getStoredToken()) {
      setCurrentUser(null);
      setIsLoading(false);
      return;
    }
    try {
      setCurrentUser(await apiRequest<AuthenticatedUser>("/auth/me"));
    } catch {
      clearStoredToken();
      setCurrentUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void refreshUser();
  }, []);

  async function login(email: string, password: string): Promise<void> {
    const token = await apiRequest<AccessTokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    storeToken(token.access_token);
    await refreshUser();
  }

  function logout(): void {
    clearStoredToken();
    setCurrentUser(null);
  }

  const value = useMemo(
    () => ({ currentUser, isLoading, login, logout, refreshUser }),
    [currentUser, isLoading],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

