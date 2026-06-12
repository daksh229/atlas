import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getToken, setToken } from "../api/client";
import { ALL_REGIONS, type AuthState, type Role, type Session } from "./types";
import { createSession } from "../api/endpoints";

const STORAGE = "bf_atlas_session";

interface AuthCtx {
  auth: AuthState | null;
  login: (role: Role, region: string) => Promise<void>;
  logout: () => void;
  setActiveRegion: (region: string) => void;
}

const Ctx = createContext<AuthCtx | undefined>(undefined);

function load(): AuthState | null {
  const token = getToken();
  const raw = localStorage.getItem(STORAGE);
  if (!token || !raw) return null;
  try {
    const s = JSON.parse(raw) as Session;
    const active = s.role === "trader" ? s.region : ALL_REGIONS;
    return { ...s, activeRegion: active };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState | null>(load);

  // keep storage in sync (active region too)
  useEffect(() => {
    if (auth) localStorage.setItem(STORAGE, JSON.stringify(auth));
  }, [auth]);

  const value = useMemo<AuthCtx>(
    () => ({
      auth,
      async login(role, region) {
        const s = await createSession(role, region);
        setToken(s.token);
        const active = s.role === "trader" ? s.region : ALL_REGIONS;
        setAuth({ ...s, activeRegion: active });
      },
      logout() {
        setToken(null);
        localStorage.removeItem(STORAGE);
        setAuth(null);
      },
      setActiveRegion(region) {
        setAuth((prev) => (prev ? { ...prev, activeRegion: region } : prev));
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
