import { useState } from "react";
import { Download } from "lucide-react";
import { useApi } from "../hooks/useApi";
import { getCatalog, downloadCatalogPdf } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader } from "../components/common";

export function BrandCatalog() {
  const { data, loading, error } = useApi(() => getCatalog(), []);
  const [busy, setBusy] = useState(false);

  async function exportPdf() {
    setBusy(true);
    try {
      await downloadCatalogPdf();
    } finally {
      setBusy(false);
    }
  }

  const byCategory =
    data?.items.reduce<Record<string, any[]>>((acc, b) => {
      (acc[b.category] ??= []).push(b);
      return acc;
    }, {}) ?? {};

  return (
    <div>
      <div className="flex items-start justify-between">
        <PageHeader
          title="📖 Brand Catalog"
          subtitle="Company-wide brand portfolio — shareable, with no internal data (no prices, clients or margins)."
        />
        <button className="btn-primary" disabled={busy || loading} onClick={exportPdf}>
          <Download size={15} /> {busy ? "Preparing…" : "Export PDF"}
        </button>
      </div>

      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : (
        <>
          <p className="text-sm text-slate-500 mb-4">{data.count} brands distributed by BF.</p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(byCategory).map(([cat, brands]) => (
              <div key={cat} className="card p-4">
                <h3 className="font-semibold text-slate-700 capitalize mb-2">
                  {cat} <span className="text-slate-400 font-normal">({brands.length})</span>
                </h3>
                <ul className="text-sm text-slate-600 space-y-1">
                  {brands.map((b) => (
                    <li key={b.brand} className="flex justify-between">
                      <span>{b.brand}</span>
                      <span className="text-slate-400">{b.products} products</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
