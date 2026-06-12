import { api } from "./client";
import { ALL_REGIONS, type Role, type Session } from "../auth/types";

// Pass region only when it is a concrete region; "All regions" => omit (manager
// cross-region). The backend enforces RBAC from the token regardless.
function regionParams(region?: string) {
  return region && region !== ALL_REGIONS ? { region } : {};
}

// ---- auth ----
export async function createSession(role: Role, region: string): Promise<Session> {
  const { data } = await api.post("/auth/session", { role, region });
  return data;
}
export async function fetchRegions(): Promise<string[]> {
  // Short timeout so onboarding fails fast if the backend isn't up.
  const { data } = await api.get("/auth/regions", { timeout: 8000 });
  return data.regions ?? [];
}

// ---- dashboard ----
export interface Kpis {
  revenue_mtd: number;
  open_deals: number;
  open_pipeline: number;
  low_stock: number;
  win_rate: number;
}
export interface Charts {
  revenue_by_region: any[];
  pipeline_by_stage: any[];
  revenue_over_time: any[];
  low_stock: any[];
  top_products: any[];
}
export async function getKpis(region?: string): Promise<Kpis> {
  const { data } = await api.get("/dashboard/kpis", { params: regionParams(region) });
  return data;
}
export async function getCharts(region?: string): Promise<Charts> {
  const { data } = await api.get("/dashboard/charts", { params: regionParams(region) });
  return data;
}

// ---- opportunities / alerts ----
export async function getOpportunities(region?: string, limit = 50) {
  const { data } = await api.get("/opportunities", {
    params: { ...regionParams(region), limit },
  });
  return data as { count: number; items: any[] };
}
export async function getAlerts(region?: string) {
  const { data } = await api.get("/alerts", { params: regionParams(region) });
  return data as { counts: Record<string, number>; items: any[] };
}

// ---- brands ----
export async function getBrandsSell(region?: string) {
  const { data } = await api.get("/brands/sell", { params: regionParams(region) });
  return data.items as any[];
}
export async function getBrandsBuy(region?: string) {
  const { data } = await api.get("/brands/buy", { params: regionParams(region) });
  return data.items as any[];
}
export async function getBrandDetail(brand: string, region?: string) {
  const { data } = await api.get(`/brands/${encodeURIComponent(brand)}`, {
    params: regionParams(region),
  });
  return data as { brand: string; best: any; offers: any[]; demands: any[] };
}

// ---- price list ----
export async function analyzePricelist(opts: {
  file?: File;
  useSample: boolean;
  preferAi: boolean;
}) {
  const form = new FormData();
  if (opts.file) form.append("file", opts.file);
  const { data } = await api.post("/pricelist/analyze", form, {
    params: { use_sample: opts.useSample, prefer_ai: opts.preferAi },
  });
  return data as {
    engine: string;
    matched: number;
    total: number;
    below_cost: number;
    items: any[];
  };
}

// ---- radar ----
export async function getRadar() {
  const { data } = await api.get("/radar");
  return data as { count: number; retailers: number; items: any[] };
}

// ---- sync ----
export async function syncAll() {
  const { data } = await api.post("/sync/all");
  return data;
}
export async function syncSource(source: string) {
  const { data } = await api.post(`/sync/${source}`);
  return data;
}
export async function getSyncStatus() {
  const { data } = await api.get("/sync/status");
  return data.items as any[];
}

// ---- chat (multi-agent) ----
export interface AgentStep {
  agent: string;
  action: string;
  detail: string;
  data?: any;
}
export interface ChatResponse {
  question: string;
  region: string | null;
  intent: string | null;
  answer: string;
  sql: string | null;
  rows: any[];
  structured: any;
  error: string | null;
  trace: AgentStep[];
}
export async function askAtlas(question: string, region?: string): Promise<ChatResponse> {
  const body = { question, region: region && region !== ALL_REGIONS ? region : null };
  const { data } = await api.post("/chat", body);
  return data;
}
