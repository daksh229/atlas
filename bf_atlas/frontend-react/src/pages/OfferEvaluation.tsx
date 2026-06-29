import { Fragment, useMemo, useState } from "react";
import { useApi } from "../hooks/useApi";
import { getOfferEvaluation } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, Pill, eur } from "../components/common";
import { KpiCard } from "../components/KpiCard";

const TONE: Record<string, string> = {
  good: "green", borderline: "amber", skip: "red", unknown: "slate",
};
const LABEL: Record<string, string> = {
  good: "Good", borderline: "Borderline", skip: "Skip", unknown: "No data",
};
const ORDER = ["good", "borderline", "skip", "unknown"];
const pct = (n: number | null | undefined) => (n == null ? "—" : `${Math.round(n * 100)}%`);

export function OfferEvaluation() {
  const { data, loading, error } = useApi(() => getOfferEvaluation(), []);
  const [file, setFile] = useState<string>("");
  const [filter, setFilter] = useState<string>("all");
  const [open, setOpen] = useState<number | null>(null);

  const files = data ? Object.keys(data.offers) : [];
  const active = file || files[0] || "";
  const rows = useMemo(() => {
    const r = data?.offers[active] ?? [];
    return filter === "all" ? r : r.filter((x) => x.verdict === filter);
  }, [data, active, filter]);

  return (
    <div>
      <PageHeader
        title="🧪 Offer Evaluation"
        subtitle="Real supplier offers judged against our purchase, sales and market data — joined on EAN, normalised to EUR via ECB rates. Unknown products are flagged, never force-matched."
      />
      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : data.error === "not_built" ? (
        <ErrorMsg message="Offer evaluation not built yet — run: python -m data.pipeline.build_offers" />
      ) : (
        <>
          <div className="flex gap-2 mb-4">
            {files.map((f) => (
              <button
                key={f}
                onClick={() => { setFile(f); setOpen(null); setFilter("all"); }}
                className={`badge ${f === active ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"}`}
              >
                {f} ({data.offers[f].length})
              </button>
            ))}
          </div>

          <div className="grid grid-cols-4 gap-4 mb-5">
            {ORDER.map((v) => {
              const n = data.report?.verdicts?.[active]?.[v] ?? 0;
              const accent = v === "good" ? "text-green-600" : v === "borderline"
                ? "text-amber-600" : v === "skip" ? "text-red-600" : "text-slate-500";
              return (
                <button key={v} onClick={() => setFilter(filter === v ? "all" : v)}
                  className={filter === v ? "ring-2 ring-brand-400 rounded-xl" : ""}>
                  <KpiCard label={LABEL[v]} value={n} accent={accent} />
                </button>
              );
            })}
          </div>

          <div className="card p-4 overflow-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-slate-400 text-xs">
                <tr>
                  <th className="py-2">Verdict</th><th>Brand</th><th>Product</th>
                  <th className="text-right">Qty</th><th className="text-right">Offer (EUR)</th>
                  <th className="text-right">Our buy</th><th className="text-right">Resale</th>
                  <th className="text-right">Margin</th><th className="text-right">Value</th>
                  <th>Who should know</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <Fragment key={i}>
                    <tr className="border-t border-slate-100 cursor-pointer hover:bg-slate-50"
                      onClick={() => setOpen(open === i ? null : i)}>
                      <td className="py-2"><Pill tone={TONE[r.verdict]}>{LABEL[r.verdict]}</Pill></td>
                      <td className="font-medium">{r.brand_surface}{r.brand_id ? "" : " ⚑"}</td>
                      <td className="text-slate-500 max-w-[260px] truncate">{r.product_name}</td>
                      <td className="text-right">{r.qty ?? "—"}</td>
                      <td className="text-right">
                        {eur(r.unit_price_eur)}
                        {r.currency !== "EUR" && (
                          <span className="text-slate-400"> · {r.unit_price?.toFixed(2)} {r.currency}</span>
                        )}
                      </td>
                      <td className="text-right">{eur(r.cost_ref_eur)}</td>
                      <td className="text-right">{eur(r.resale_ref_eur)}</td>
                      <td className={`text-right font-semibold ${r.margin_pct >= 0.25 ? "text-green-600" : r.margin_pct >= 0.1 ? "text-amber-600" : "text-red-600"}`}>{pct(r.margin_pct)}</td>
                      <td className="text-right">{eur(r.potential_value_eur)}</td>
                      <td className="text-slate-500">
                        {r.sell_side?.length ? "→ " + r.sell_side.slice(0, 2).join(", ")
                          : r.sources?.length ? "⇠ " + r.sources.slice(0, 2).join(", ") : "—"}
                      </td>
                    </tr>
                    {open === i && (
                      <tr className="bg-slate-50/60">
                        <td colSpan={10} className="px-3 py-3">
                          <div className="text-slate-700 mb-2">{r.why}</div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                            <Fact k="EAN" v={r.ean ?? "—"} />
                            <Fact k="Cost basis" v={r.cost_basis ?? "—"} />
                            <Fact k="Resale basis" v={r.resale_basis ?? "—"} />
                            <Fact k="Market min" v={eur(r.market_min_eur)} />
                            <Fact k="Sources (bought before)" v={r.sources?.join(", ") || "—"} />
                            <Fact k="Sell-side (sold before)" v={r.sell_side?.join(", ") || "—"} />
                            <Fact k="Clients" v={r.n_clients ? `${r.n_clients} (names masked)` : "—"} />
                            {r.flags?.length > 0 && <Fact k="Flags" v={r.flags.join(", ")} />}
                            {r.brand_context && (
                              <Fact k="Brand-level context"
                                v={`buy ~${eur(r.brand_context.typical_buy_eur)} · sell ~${eur(r.brand_context.typical_sale_eur)} · ${r.brand_context.n_products} products`} />
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-400 mt-3">
            FX: ECB reference rates ({data.report?.fx_source}). ⚑ = brand not in our dictionary.
            Client names are access-controlled — only a count is shown.
          </p>
        </>
      )}
    </div>
  );
}

function Fact({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <div className="text-slate-400 uppercase tracking-wide text-[10px]">{k}</div>
      <div className="text-slate-700">{v}</div>
    </div>
  );
}
