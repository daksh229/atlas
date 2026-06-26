import { useNavigate } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { getBrandsBuy, getBrandsSell } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, eur } from "../components/common";

function BrandTable({
  rows,
  cols,
}: {
  rows: any[];
  cols: { key: string; label: string; fmt?: (v: any) => string; align?: string }[];
}) {
  const navigate = useNavigate();
  if (!rows?.length) return <p className="text-slate-400 text-sm py-6">No brands in your scope.</p>;
  return (
    <div className="overflow-auto border border-slate-100 rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-500 text-xs">
          <tr>
            {cols.map((c) => (
              <th key={c.key} className={`px-3 py-2 ${c.align === "right" ? "text-right" : ""}`}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.brand_id}
              className="border-t border-slate-100 hover:bg-brand-50 cursor-pointer"
              onClick={() => navigate(`/brand/${r.brand_id}`)}
            >
              {cols.map((c) => (
                <td key={c.key} className={`px-3 py-2 ${c.align === "right" ? "text-right" : ""}`}>
                  {c.fmt ? c.fmt(r[c.key]) : r[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function BrandsSell() {
  const { data, loading, error } = useApi(() => getBrandsSell(), []);
  return (
    <div>
      <PageHeader title="💰 Brands I Can Sell" subtitle="Where your clients show demand — click a brand for full intelligence." />
      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : (
        <div className="card p-4">
          <BrandTable
            rows={data}
            cols={[
              { key: "brand", label: "Brand" },
              { key: "category", label: "Category" },
              { key: "clients", label: "Clients", align: "right" },
              { key: "avg_target_price", label: "Avg target", align: "right", fmt: eur },
              { key: "total_wanted", label: "Units wanted", align: "right" },
            ]}
          />
        </div>
      )}
    </div>
  );
}

export function BrandsBuy() {
  const { data, loading, error } = useApi(() => getBrandsBuy(), []);
  return (
    <div>
      <PageHeader title="🛒 Brands I Can Buy" subtitle="What your suppliers can source — click a brand for full intelligence." />
      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : (
        <div className="card p-4">
          <BrandTable
            rows={data}
            cols={[
              { key: "brand", label: "Brand" },
              { key: "category", label: "Category" },
              { key: "offers", label: "Offers", align: "right" },
              { key: "best_buy_price", label: "Best buy", align: "right", fmt: eur },
              { key: "total_available", label: "Available", align: "right" },
            ]}
          />
        </div>
      )}
    </div>
  );
}
