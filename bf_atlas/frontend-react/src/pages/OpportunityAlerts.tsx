import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "../auth/AuthContext";
import { ALL_REGIONS } from "../auth/types";
import { useApi } from "../hooks/useApi";
import { getAlerts, getOpportunities } from "../api/endpoints";
import { DirectionalNote, ErrorMsg, Loading, PageHeader, eur } from "../components/common";
import { KpiCard } from "../components/KpiCard";

const ICON: Record<string, string> = {
  "Buy↔Sell Match": "💹",
  "Price Drop": "📉",
  "New Demand": "🆕",
  "New Supply": "📦",
  "Low Stock + Demand": "⚠️",
  "Stalled Deal": "💤",
};

export function OpportunityAlerts() {
  const { auth } = useAuth();
  const region = auth!.activeRegion;
  const scope = region === ALL_REGIONS ? "all regions" : region;

  const alerts = useApi(() => getAlerts(region), [region]);
  const opps = useApi(() => getOpportunities(region), [region]);

  return (
    <div>
      <PageHeader
        title="🚨 Opportunity Alerts"
        subtitle={`Cross-match engine — supplier offers ↔ client demand · scoped to ${scope}`}
      />
      <DirectionalNote />

      {(alerts.error || opps.error) && <ErrorMsg message={alerts.error || opps.error!} />}
      {alerts.loading || opps.loading || !alerts.data || !opps.data ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4">
            <KpiCard label="Live alerts" value={alerts.data.items.length} />
            <KpiCard
              label="Open match value"
              value={eur(opps.data.items.reduce((s, o) => s + (o.margin_value || 0), 0))}
            />
            <KpiCard label="Alert types firing" value={Object.keys(alerts.data.counts).length} />
          </div>

          <div className="grid lg:grid-cols-5 gap-4 mt-6">
            <div className="card p-4 lg:col-span-2">
              <h3 className="font-semibold text-slate-700 mb-3">Alerts by type</h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart
                  layout="vertical"
                  data={Object.entries(alerts.data.counts).map(([type, count]) => ({ type, count }))}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} fontSize={11} />
                  <YAxis type="category" dataKey="type" width={120} fontSize={10} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#6c5ce7" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-4 lg:col-span-3">
              <h3 className="font-semibold text-slate-700 mb-3">Top cross-match opportunities</h3>
              <div className="overflow-auto max-h-72">
                <table className="w-full text-sm">
                  <thead className="text-left text-slate-400 text-xs">
                    <tr>
                      <th className="py-1">Brand</th><th>Supplier → Client</th>
                      <th className="text-right">Buy</th><th className="text-right">Sell</th>
                      <th className="text-right">Margin</th>
                    </tr>
                  </thead>
                  <tbody>
                    {opps.data.items.slice(0, 10).map((o, i) => (
                      <tr key={i} className="border-t border-slate-100">
                        <td className="py-1.5 font-medium">{o.brand}</td>
                        <td className="text-slate-500 text-xs">{o.supplier} → {o.client}</td>
                        <td className="text-right">{eur(o.buy_price)}</td>
                        <td className="text-right">{eur(o.sell_price)}</td>
                        <td className="text-right font-semibold text-green-600">{eur(o.margin_value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* alert feed grouped by type */}
          <div className="mt-6 space-y-3">
            {Object.keys(alerts.data.counts).map((type) => {
              const rows = alerts.data!.items.filter((a) => a.type === type);
              return (
                <div key={type} className="card p-4">
                  <h4 className="font-semibold text-slate-700 mb-2">
                    {ICON[type] || "•"} {type} <span className="text-slate-400 font-normal">({rows.length})</span>
                  </h4>
                  <ul className="space-y-1 text-sm text-slate-600">
                    {rows.map((a, i) => (
                      <li key={i} className="flex justify-between gap-3">
                        <span>{a.detail}</span>
                        {a.value != null && <span className="font-semibold text-slate-800 whitespace-nowrap">{eur(a.value)}</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
