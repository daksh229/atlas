import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApi } from "../hooks/useApi";
import { getDashboard } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, eur } from "../components/common";
import { KpiCard } from "../components/KpiCard";

export function Overview() {
  const { data, loading, error } = useApi(() => getDashboard(), []);
  return (
    <div>
      <PageHeader title="📊 Overview" subtitle="Your slice of BF — scoped to your own accounts." />
      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="My clients" value={data.kpis.clients} />
            <KpiCard label="My suppliers" value={data.kpis.suppliers} />
            <KpiCard label="Open demand signals" value={data.kpis.open_demand_signals} />
            <KpiCard label="Revenue (my orders)" value={eur(data.kpis.revenue_total)} />
          </div>

          <div className="card p-4 mt-6">
            <h3 className="font-semibold text-slate-700 mb-3">My most active brands</h3>
            {data.my_brands.length === 0 ? (
              <p className="text-slate-400 text-sm py-6">No active brands yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.my_brands}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="brand" fontSize={10} angle={-25} textAnchor="end" height={70} />
                  <YAxis fontSize={11} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="demand" stackId="a" fill="#6c5ce7" name="Demand signals" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="supply" stackId="a" fill="#a29bfe" name="Supply signals" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      )}
    </div>
  );
}
