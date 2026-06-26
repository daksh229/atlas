import { useApi } from "../hooks/useApi";
import { getMySuppliers } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, eur } from "../components/common";

export function MySuppliers() {
  const { data, loading, error } = useApi(() => getMySuppliers(), []);
  return (
    <div>
      <PageHeader title="🚚 My Suppliers" subtitle="Your own sourcing accounts only — scoped server-side to you." />
      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : !data.length ? (
        <div className="card p-6 text-center text-slate-500">No suppliers assigned to you.</div>
      ) : (
        <div className="card p-4 overflow-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-slate-400 text-xs">
              <tr>
                <th className="py-2">Supplier</th>
                <th>Country</th>
                <th className="text-right">Purchase orders</th>
                <th className="text-right">Total purchased</th>
                <th className="text-right">Active offers</th>
                <th className="text-right">Best offer</th>
              </tr>
            </thead>
            <tbody>
              {data.map((s) => (
                <tr key={s.id} className="border-t border-slate-100">
                  <td className="py-2 font-medium">{s.supplier}</td>
                  <td className="text-slate-500">{s.country}</td>
                  <td className="text-right">{s.purchase_orders}</td>
                  <td className="text-right font-semibold">{eur(s.total_purchased)}</td>
                  <td className="text-right">{s.active_offers}</td>
                  <td className="text-right">{eur(s.best_offer)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
