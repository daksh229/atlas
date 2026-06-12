import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Euro, Handshake, PackageX, Trophy, Siren } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { ALL_REGIONS } from "../auth/types";
import { useApi } from "../hooks/useApi";
import { getAlerts, getCharts, getKpis, getOpportunities } from "../api/endpoints";
import { KpiCard } from "../components/KpiCard";
import { DirectionalNote, ErrorMsg, Loading, eur } from "../components/common";

const BRAND = "#6c5ce7";

export function Dashboard() {
  const { auth } = useAuth();
  const region = auth!.activeRegion;
  const scopeLabel = region === ALL_REGIONS ? "all regions" : region;

  const kpis = useApi(() => getKpis(region), [region]);
  const charts = useApi(() => getCharts(region), [region]);
  const alerts = useApi(() => getAlerts(region), [region]);
  const opps = useApi(() => getOpportunities(region), [region]);

  return (
    <div>
      <PageTitle scope={scopeLabel} />
      <DirectionalNote />

      {kpis.error && <ErrorMsg message={kpis.error} />}
      {kpis.loading || !kpis.data ? (
        <Loading />
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard label="Revenue (MTD)" value={eur(kpis.data.revenue_mtd)} icon={<Euro size={18} />} />
          <KpiCard
            label="Open Deals"
            value={kpis.data.open_deals}
            sub={`${eur(kpis.data.open_pipeline)} pipeline`}
            icon={<Handshake size={18} />}
          />
          <KpiCard label="Low-Stock SKUs" value={kpis.data.low_stock} icon={<PackageX size={18} />} accent="text-amber-500" />
          <KpiCard label="Win Rate" value={`${kpis.data.win_rate.toFixed(1)}%`} icon={<Trophy size={18} />} />
        </div>
      )}

      {/* Atlas opportunity strip */}
      {!opps.loading && opps.data && !alerts.loading && alerts.data && (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
          <KpiCard label="Live alerts" value={alerts.data.items.length} icon={<Siren size={18} />} accent="text-red-500" />
          <KpiCard
            label="Cross-match value"
            value={eur(opps.data.items.reduce((s, o) => s + (o.margin_value || 0), 0))}
          />
          <KpiCard label="Opportunities" value={opps.data.count} />
        </div>
      )}

      {/* charts */}
      {charts.error && <div className="mt-4"><ErrorMsg message={charts.error} /></div>}
      {charts.loading || !charts.data ? (
        <Loading />
      ) : (
        <>
          <div className="grid lg:grid-cols-2 gap-4 mt-6">
            <ChartCard title="Revenue by region">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={charts.data.revenue_by_region}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="region" fontSize={11} />
                  <YAxis fontSize={11} tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v: number) => eur(v)} />
                  <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
                    {charts.data.revenue_by_region.map((r) => (
                      <Cell key={r.region} fill={region === ALL_REGIONS || r.region === region ? BRAND : "#cbd5e1"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Pipeline by stage">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={charts.data.pipeline_by_stage} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" fontSize={11} tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
                  <YAxis type="category" dataKey="stage" fontSize={11} width={80} />
                  <Tooltip formatter={(v: number) => eur(v)} />
                  <Bar dataKey="value" fill={BRAND} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <ChartCard title="Revenue over time" className="mt-4">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={charts.data.revenue_over_time}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" fontSize={11} />
                <YAxis fontSize={11} tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: number) => eur(v)} />
                <Line type="monotone" dataKey="revenue" stroke={BRAND} strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <div className="grid lg:grid-cols-2 gap-4 mt-4">
            <ChartCard title="⚠️ Low-stock alerts">
              <div className="overflow-auto max-h-72">
                <table className="w-full text-sm">
                  <thead className="text-left text-slate-400 text-xs">
                    <tr><th className="py-1">Product</th><th>Region</th><th className="text-right">Avail</th></tr>
                  </thead>
                  <tbody>
                    {charts.data.low_stock.length === 0 ? (
                      <tr><td colSpan={3} className="text-slate-400 py-3">No SKUs below threshold.</td></tr>
                    ) : (
                      charts.data.low_stock.slice(0, 30).map((r, i) => (
                        <tr key={i} className="border-t border-slate-100">
                          <td className="py-1.5">{r.product}</td>
                          <td className="text-slate-500">{r.region}</td>
                          <td className="text-right font-medium text-amber-600">{r.qty_available}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </ChartCard>

            <ChartCard title="Top products">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[...charts.data.top_products].reverse()} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" fontSize={11} tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
                  <YAxis type="category" dataKey="product" fontSize={10} width={140} />
                  <Tooltip formatter={(v: number) => eur(v)} />
                  <Bar dataKey="revenue" fill={BRAND} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
        </>
      )}
    </div>
  );
}

function PageTitle({ scope }: { scope: string }) {
  return (
    <div className="mb-5">
      <h1 className="text-2xl font-bold text-slate-900">📊 Trader Dashboard</h1>
      <p className="text-slate-500 text-sm mt-1">
        Unified Odoo + NetHunt view — scoped to <strong>{scope}</strong>
      </p>
    </div>
  );
}

function ChartCard({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`card p-4 ${className}`}>
      <h3 className="font-semibold text-slate-700 mb-3">{title}</h3>
      {children}
    </div>
  );
}
