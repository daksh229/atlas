import { useApi } from "../hooks/useApi";
import { getAlerts } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, eur } from "../components/common";
import { KpiCard } from "../components/KpiCard";

const TYPE_STYLE: Record<string, { icon: string; ring: string }> = {
  triple_match: { icon: "🎯", ring: "border-l-purple-500" },
  offer_to_request: { icon: "✉️", ring: "border-l-blue-500" },
  demand_supply: { icon: "💹", ring: "border-l-green-500" },
  stock_match: { icon: "📦", ring: "border-l-teal-500" },
  external_market: { icon: "🛰️", ring: "border-l-amber-500" },
  reorder: { icon: "🔁", ring: "border-l-slate-400" },
};

export function OpportunityAlerts() {
  const { data, loading, error } = useApi(() => getAlerts(), []);

  return (
    <div>
      <PageHeader
        title="🚨 Opportunity Alerts"
        subtitle="Routed to you, ranked by priority, bundled by brand — your daily action list."
      />

      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Alerts for you" value={data.total} />
            <KpiCard label="Alert types firing" value={Object.keys(data.counts).length} />
            <KpiCard
              label="Top type"
              value={Object.entries(data.counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—"}
            />
            <KpiCard
              label="Suppressed (daily cap)"
              value={data.suppressed}
              sub="kept out of the feed to avoid noise"
            />
          </div>

          <div className="mt-6 space-y-3">
            {data.items.length === 0 && (
              <div className="card p-6 text-center text-slate-500">
                No alerts in your scope right now.
              </div>
            )}
            {data.items.map((a) => {
              const s = TYPE_STYLE[a.type] ?? { icon: "•", ring: "border-l-slate-300" };
              return (
                <div key={a.id} className={`card p-4 border-l-4 ${s.ring}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-slate-800">
                      {s.icon} {a.label}{" "}
                      <span className="text-slate-400 font-normal">· {a.brand}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {a.value > 0 && (
                        <span className="font-semibold text-green-600">{eur(a.value)}</span>
                      )}
                      <span className="badge bg-slate-100 text-slate-500">P{a.priority}</span>
                      {a.items.length > 1 && (
                        <span className="badge bg-brand-50 text-brand-700">
                          {a.items.length} matches
                        </span>
                      )}
                    </div>
                  </div>
                  <ul className="space-y-1 text-sm text-slate-600">
                    {a.items.map((line, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-slate-300">›</span>
                        <span>{line}</span>
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
