import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type AuthContextValue = {
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const TOKEN_KEY = "receiptslegder_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));

  const value = useMemo(
    () => ({
      token,
      setToken: (next: string | null) => {
        if (next) {
          localStorage.setItem(TOKEN_KEY, next);
        } else {
          localStorage.removeItem(TOKEN_KEY);
        }
        setTokenState(next);
      },
      logout: () => {
        localStorage.removeItem(TOKEN_KEY);
        setTokenState(null);
      },
    }),
    [token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
