export type Verdict = "good" | "borderline" | "skip" | "unknown";

export interface OfferRow {
  source_file: string;
  supplier_name: string;
  brand_surface: string;
  brand_id: string | null;
  ean: string | null;
  product_name: string;
  size: string | null;
  qty: number | null;
  unit_price: number | null;
  currency: string;
  unit_price_eur: number | null;
  offer_date: string | null;
  is_comparable: boolean;
  matched: boolean;
  verdict: Verdict;
  cost_ref_eur: number | null;
  cost_basis: string | null;
  cost_delta_pct: number | null;
  resale_ref_eur: number | null;
  resale_basis: string | null;
  margin_pct: number | null;
  market_min_eur: number | null;
  market_margin_pct: number | null;
  potential_value_eur: number | null;
  sources: string[];
  sell_side: string[];
  n_clients: number;
  brand_context: {
    brand: string;
    typical_buy_eur: number | null;
    typical_sale_eur: number | null;
    n_products: number;
  } | null;
  why: string;
  flags: string[];
}

export interface Payload {
  offers: Record<string, OfferRow[]>;
  report: any;
}
