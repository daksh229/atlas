import { useApi } from "../hooks/useApi";
import { getMyClients } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, eur } from "../components/common";

export function MyClients() {
  const { data, loading, error } = useApi(() => getMyClients(), []);
  return (
    <div>
      <PageHeader title="👤 My Clients" subtitle="Your own accounts only — other traders' clients are never shown here." />
      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : !data.length ? (
        <div className="card p-6 text-center text-slate-500">No clients assigned to you.</div>
      ) : (
        <div className="card p-4 overflow-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-slate-400 text-xs">
              <tr>
                <th className="py-2">Client</th>
                <th>Country</th>
                <th className="text-right">Orders</th>
                <th className="text-right">Lifetime value</th>
                <th className="text-right">Open demands</th>
                <th>Last order</th>
              </tr>
            </thead>
            <tbody>
              {data.map((c) => (
                <tr key={c.id} className="border-t border-slate-100">
                  <td className="py-2 font-medium">{c.client}</td>
                  <td className="text-slate-500">{c.country}</td>
                  <td className="text-right">{c.orders}</td>
                  <td className="text-right font-semibold">{eur(c.lifetime_value)}</td>
                  <td className="text-right">{c.open_demands}</td>
                  <td className="text-slate-500">{c.last_order ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
