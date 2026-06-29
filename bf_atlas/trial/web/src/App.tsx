import { Fragment, useEffect, useMemo, useState } from "react";
import type { OfferRow, Payload, Verdict } from "./types";

const VERDICT_ORDER: Verdict[] = ["good", "borderline", "skip", "unknown"];
const VERDICT_LABEL: Record<Verdict, string> = {
  good: "Good", borderline: "Borderline", skip: "Skip", unknown: "No data",
};

const eur = (n: number | null | undefined) =>
  n == null ? "—" : "€" + n.toLocaleString("en", { maximumFractionDigits: 2 });
const pct = (n: number | null | undefined) =>
  n == null ? "—" : (n * 100).toFixed(0) + "%";

export default function App() {
  const [data, setData] = useState<Payload | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [file, setFile] = useState<string>("");
  const [filter, setFilter] = useState<Verdict | "all">("all");
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    fetch("/offer_evaluation.json")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((d: Payload) => {
        setData(d);
        setFile(Object.keys(d.offers)[0]);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  const rows = useMemo<OfferRow[]>(() => {
    if (!data || !file) return [];
    const r = data.offers[file] ?? [];
    return filter === "all" ? r : r.filter((x) => x.verdict === filter);
  }, [data, file, filter]);

  if (err)
    return (
      <div className="wrap">
        <h1>BF Atlas — Offer Evaluator</h1>
        <p className="error">
          Could not load <code>/offer_evaluation.json</code> ({err}). Run{" "}
          <code>python -m data.pipeline.build_offers</code> first.
        </p>
      </div>
    );
  if (!data) return <div className="wrap">Loading…</div>;

  const counts = data.report?.verdicts?.[file] ?? {};
  const total = Object.values(counts).reduce((a: number, b: any) => a + b, 0);

  return (
    <div className="wrap">
      <header>
        <h1>BF Atlas — Supplier Offer Evaluator</h1>
        <p className="sub">
          Is this offer worth pursuing — and who internally should know? Every
          number is BF's own history (purchases, sales, retailer market),
          joined on EAN, normalized to EUR via ECB rates.
        </p>
      </header>

      <nav className="tabs">
        {Object.keys(data.offers).map((f) => (
          <button
            key={f}
            className={f === file ? "tab on" : "tab"}
            onClick={() => { setFile(f); setOpen(null); setFilter("all"); }}
          >
            {f} <span className="muted">({data.offers[f].length})</span>
          </button>
        ))}
      </nav>

      <section className="kpis">
        {VERDICT_ORDER.map((v) => (
          <button
            key={v}
            className={"kpi " + v + (filter === v ? " sel" : "")}
            onClick={() => setFilter(filter === v ? "all" : v)}
          >
            <span className="kpi-n">{counts[v] ?? 0}</span>
            <span className="kpi-l">{VERDICT_LABEL[v]}</span>
          </button>
        ))}
        <div className="kpi total">
          <span className="kpi-n">{total}</span>
          <span className="kpi-l">Lines</span>
        </div>
      </section>

      <table>
        <thead>
          <tr>
            <th>Verdict</th><th>Brand</th><th>Product</th><th className="r">Qty</th>
            <th className="r">Offer (EUR)</th><th className="r">Our avg buy</th>
            <th className="r">Resale ref</th><th className="r">Margin</th>
            <th className="r">Value</th><th>Who should know</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <Fragment key={i}>
              <tr className="row" onClick={() => setOpen(open === i ? null : i)}>
                <td><span className={"pill " + r.verdict}>{VERDICT_LABEL[r.verdict]}</span></td>
                <td>{r.brand_surface}{r.brand_id ? "" : " ⚑"}</td>
                <td className="prod">{r.product_name}</td>
                <td className="r">{r.qty ?? "—"}</td>
                <td className="r">
                  {eur(r.unit_price_eur)}
                  {r.currency !== "EUR" && (
                    <span className="muted"> · {r.unit_price?.toFixed(2)} {r.currency}</span>
                  )}
                </td>
                <td className="r">{eur(r.cost_ref_eur)}</td>
                <td className="r">{eur(r.resale_ref_eur)}</td>
                <td className={"r " + marginClass(r.margin_pct)}>{pct(r.margin_pct)}</td>
                <td className="r">{eur(r.potential_value_eur)}</td>
                <td className="who">{whoShort(r)}</td>
              </tr>
              {open === i && (
                <tr className="detail">
                  <td colSpan={10}>
                    <div className="why">{r.why}</div>
                    <div className="grid">
                      <Fact k="EAN" v={r.ean ?? "—"} />
                      <Fact k="Cost basis" v={r.cost_basis ?? "—"} />
                      <Fact k="Resale basis" v={r.resale_basis ?? "—"} />
                      <Fact k="Market min" v={eur(r.market_min_eur)} />
                      <Fact k="Margin vs market" v={pct(r.market_margin_pct)} />
                      <Fact k="Sources (bought before)" v={r.sources.join(", ") || "—"} />
                      <Fact k="Sell-side (sold before)" v={r.sell_side.join(", ") || "—"} />
                      <Fact k="Clients" v={r.n_clients ? `${r.n_clients} (names masked)` : "—"} />
                      {r.flags.length > 0 && <Fact k="Flags" v={r.flags.join(", ")} />}
                      {r.brand_context && (
                        <Fact
                          k="Brand-level context"
                          v={`buy ~${eur(r.brand_context.typical_buy_eur)} · sell ~${eur(
                            r.brand_context.typical_sale_eur
                          )} · ${r.brand_context.n_products} products`}
                        />
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
      <footer className="muted">
        FX: ECB reference rates ({data.report?.fx_source}). ⚑ = brand not in our
        dictionary. Margin bands and bases are configurable in the pipeline.
      </footer>
    </div>
  );
}

function Fact({ k, v }: { k: string; v: string }) {
  return (
    <div className="fact">
      <span className="fk">{k}</span>
      <span className="fv">{v}</span>
    </div>
  );
}

function whoShort(r: OfferRow): string {
  if (r.sell_side.length) return "→ " + r.sell_side.slice(0, 2).join(", ");
  if (r.sources.length) return "⇠ " + r.sources.slice(0, 2).join(", ");
  return "—";
}

function marginClass(m: number | null): string {
  if (m == null) return "";
  if (m >= 0.25) return "pos";
  if (m >= 0.1) return "mid";
  return "neg";
}
