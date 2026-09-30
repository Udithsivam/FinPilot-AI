import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useState, type ReactNode } from "react";

import { api, ApiError, getToken, setToken as persistToken } from "@/lib/api";
import type { User } from "@/types/api";

interface AuthContextValue {
  user: User | undefined;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [hasToken, setHasToken] = useState(() => Boolean(getToken()));

  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: api.me,
    enabled: hasToken,
    retry: false,
    staleTime: 5 * 60 * 1000,
    throwOnError: (error) => {
      if (error instanceof ApiError && error.status === 401) {
        persistToken(null);
        setHasToken(false);
      }
      return false;
    },
  });

  async function login(email: string, password: string) {
    const token = await api.login(email, password);
    persistToken(token.access_token);
    setHasToken(true);
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  async function register(email: string, password: string, fullName: string) {
    await api.register(email, password, fullName);
    await login(email, password);
  }

  function logout() {
    persistToken(null);
    setHasToken(false);
    queryClient.clear();
  }

  return (
    <AuthContext.Provider
      value={{ user, isLoading: hasToken && isLoading, isAuthenticated: Boolean(user), login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
