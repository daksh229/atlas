import { api } from "./client";
import type { Session, Trader } from "../auth/types";

// ---- auth / onboarding ----
export async function getTraders(): Promise<Trader[]> {
  const { data } = await api.get("/auth/traders", { timeout: 8000 });
  return data.traders ?? [];
}
export async function createSession(traderId: string): Promise<Session> {
  const { data } = await api.post("/auth/session", { trader_id: traderId });
  return data;
}

// ---- Opportunity Alerts (routed, bundled, capped) ----
export interface AlertBundle {
  id: string;
  type: string;
  label: string;
  brand: string;
  brand_id: string;
  priority: number;
  value: number;
  items: string[];
}
export interface AlertFeed {
  trader: string;
  total: number;
  suppressed: number;
  counts: Record<string, number>;
  items: AlertBundle[];
}
export async function getAlerts(): Promise<AlertFeed> {
  const { data } = await api.get("/alerts");
  return data;
}

// ---- Brand Maps + Brand Intelligence ----
export async function getBrandsSell() {
  const { data } = await api.get("/brands/sell");
  return data.items as any[];
}
export async function getBrandsBuy() {
  const { data } = await api.get("/brands/buy");
  return data.items as any[];
}
export async function getBrandDetail(brandId: string) {
  const { data } = await api.get(`/brands/${encodeURIComponent(brandId)}`);
  return data as {
    brand_id: string;
    brand: string;
    category: string;
    best_historical_sell_price: number | null;
    colleagues: any[];
    demands: any[];
    offers: any[];
    retailers: any[];
  };
}

// ---- My Relationships ----
export async function getMyClients() {
  const { data } = await api.get("/relationships/clients");
  return data.items as any[];
}
export async function getMySuppliers() {
  const { data } = await api.get("/relationships/suppliers");
  return data.items as any[];
}

// ---- Offers Inbox (structural) ----
export async function getOffers() {
  const { data } = await api.get("/offers");
  return data.items as any[];
}
export async function submitOffer(brand: string, offer_price: number, qty: number) {
  const { data } = await api.post("/offers", { brand, offer_price, qty });
  return data as {
    ok: boolean;
    error?: string;
    brand?: string;
    match_count?: number;
    matches?: any[];
  };
}
export async function getInbox() {
  const { data } = await api.get("/offers/inbox");
  return data.items as { id: string; from: string; subject: string; preview: string }[];
}
export async function getEmail(id: string) {
  const { data } = await api.get(`/offers/inbox/${encodeURIComponent(id)}`);
  return data as { id: string; from: string; subject: string; body: string };
}
export async function parseEmail(email_id: string) {
  // AI extraction can take a few seconds — give it room beyond the default timeout.
  const { data } = await api.post("/offers/parse", { email_id }, { timeout: 60000 });
  return data as { engine: string | null; offers: any[]; error?: string };
}
export async function acceptOffers(offers: any[]) {
  const { data } = await api.post("/offers/accept", { offers });
  return data as { accepted: number; skipped: number; match_count: number; matches: any[] };
}

// ---- Supplier-offer evaluation (the 3 real offers judged vs our data) ----
export async function getOfferEvaluation() {
  const { data } = await api.get("/offers/evaluation");
  return data as {
    offers: Record<string, any[]>;
    report: { verdicts?: Record<string, Record<string, number>>; fx_source?: string };
    error?: string;
  };
}

// ---- Retailer Radar ----
export async function getRadar() {
  const { data } = await api.get("/radar");
  return data as {
    count: number;
    market_windows: number;
    unknown_brands: number;
    items: any[];
  };
}

// ---- Brand Catalog ----
export async function getCatalog() {
  const { data } = await api.get("/catalog");
  return data as { count: number; items: any[] };
}
export async function downloadCatalogPdf() {
  const res = await api.get("/catalog/pdf", { responseType: "blob" });
  const type = String(res.headers["content-type"] || "application/pdf");
  const ext = type.includes("pdf") ? "pdf" : "txt";
  const url = URL.createObjectURL(new Blob([res.data], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = `bf_brand_catalogue.${ext}`;
  a.click();
  URL.revokeObjectURL(url);
}

// ---- My View (dashboard) ----
export async function getDashboard() {
  const { data } = await api.get("/dashboard");
  return data as { kpis: Record<string, number>; my_brands: any[] };
}
