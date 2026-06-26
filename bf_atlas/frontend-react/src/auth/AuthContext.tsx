import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getToken, setToken } from "../api/client";
import type { AuthState, Session } from "./types";
import { createSession } from "../api/endpoints";

const STORAGE = "bf_atlas_session";

interface AuthCtx {
  auth: AuthState | null;
  login: (traderId: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | undefined>(undefined);

function load(): AuthState | null {
  const token = getToken();
  const raw = localStorage.getItem(STORAGE);
  if (!token || !raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState | null>(load);

  useEffect(() => {
    if (auth) localStorage.setItem(STORAGE, JSON.stringify(auth));
  }, [auth]);

  const value = useMemo<AuthCtx>(
    () => ({
      auth,
      async login(traderId) {
        const s = await createSession(traderId);
        setToken(s.token);
        setAuth(s);
      },
      logout() {
        setToken(null);
        localStorage.removeItem(STORAGE);
        setAuth(null);
      },
    }),
    [auth]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
