import { useApi } from "../hooks/useApi";
import { getRadar } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, eur } from "../components/common";
import { KpiCard } from "../components/KpiCard";

export function RetailerRadar() {
  const { data, loading, error } = useApi(() => getRadar(), []);
  return (
    <div>
      <PageHeader
        title="🛰️ Retailer Radar"
        subtitle="Retailer prices vs. what we can supply for. Brands we don't recognise are flagged, not guessed."
      />
      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4 mb-5">
            <KpiCard label="Rows scanned" value={data.count} />
            <KpiCard label="Market windows" value={data.market_windows} accent="text-green-600" />
            <KpiCard label="Unknown brands flagged" value={data.unknown_brands} accent="text-amber-600" />
          </div>
          <div className="card p-4 overflow-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-slate-400 text-xs">
                <tr>
                  <th className="py-2">Retailer</th>
                  <th>Brand</th>
                  <th>Product</th>
                  <th className="text-right">Retail</th>
                  <th className="text-right">Our buy</th>
                  <th className="text-right">Headroom</th>
                  <th>Signal</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="py-2">{r.retailer}</td>
                    <td className="font-medium">{r.brand}</td>
                    <td className="text-slate-500">{r.product}</td>
                    <td className="text-right">{eur(r.retail_price)}</td>
                    <td className="text-right">{eur(r.our_buy_price)}</td>
                    <td className="text-right font-semibold">
                      {r.headroom_per_unit != null ? eur(r.headroom_per_unit) : "—"}
                    </td>
                    <td>{r.signal}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
