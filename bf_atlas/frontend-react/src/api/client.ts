import axios from "axios";

const BASE = import.meta.env.VITE_API_URL || "/api";
const TOKEN_KEY = "bf_atlas_token";

// 30s default covers AI/chat calls; individual calls can override (see endpoints).
export const api = axios.create({ baseURL: BASE, timeout: 30000 });

// Attach the JWT session token (set at onboarding) to every request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
