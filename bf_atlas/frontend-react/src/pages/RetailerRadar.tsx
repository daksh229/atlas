import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ShieldCheck } from "lucide-react";
import { useApi } from "../hooks/useApi";
import { getRadar } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, eur } from "../components/common";

export function RetailerRadar() {
  const { data, loading, error } = useApi(() => getRadar(), []);

  return (
    <div>
      <PageHeader
        title="📡 Retailer Radar"
        subtitle="Daily competitor price scan across retailers, compared to our list price."
      />

      <div className="mb-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 flex gap-2">
        <ShieldCheck size={18} className="shrink-0 mt-0.5" />
        <span>
          <strong>Honest scope:</strong> <em>LuxeScent (live parser)</em> rows come from a real BeautifulSoup
          scraper on a local fixture — the same code parses a live URL. All <em>(mock)</em> retailers are
          placeholder data. Production would add per-retailer parsers, robots.txt/ToS compliance, rate-limiting,
          and a scheduled daily run.
        </span>
      </div>

      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Stat label="Retailers" value={data.retailers} />
            <Stat label="Products tracked" value={data.count} />
            <Stat label="We're undercut on" value={data.items.filter((r) => r.signal?.includes("Retailer cheaper")).length} />
          </div>

          <div className="grid lg:grid-cols-5 gap-4">
            <div className="card p-4 lg:col-span-3 overflow-auto max-h-[28rem]">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-left text-slate-500 text-xs sticky top-0">
                  <tr>
                    <th className="px-3 py-2">Retailer</th><th className="px-3 py-2">Product</th>
                    <th className="px-3 py-2 text-right">Retail</th><th className="px-3 py-2 text-right">Ours</th>
                    <th className="px-3 py-2">Signal</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((r, i) => (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="px-3 py-1.5 text-slate-500">{r.retailer}</td>
                      <td className="px-3 py-1.5">{r.product}</td>
                      <td className="px-3 py-1.5 text-right">{eur(r.retail_price)}</td>
                      <td className="px-3 py-1.5 text-right">{r.our_list_price != null ? eur(r.our_list_price) : "—"}</td>
                      <td className="px-3 py-1.5 whitespace-nowrap">{r.signal}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card p-4 lg:col-span-2">
              <h3 className="font-semibold text-slate-700 mb-3">Price gap vs our list</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  layout="vertical"
                  data={data.items
                    .filter((r) => r.gap_vs_us != null)
                    .map((r) => ({ name: `${r.product.slice(0, 18)} · ${r.retailer.split(" ")[0]}`, gap: r.gap_vs_us }))}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" fontSize={11} />
                  <YAxis type="category" dataKey="name" width={150} fontSize={9} />
                  <Tooltip formatter={(v: number) => eur(v)} />
                  <Bar dataKey="gap">
                    {data.items
                      .filter((r) => r.gap_vs_us != null)
                      .map((r, i) => (
                        <Cell key={i} fill={r.gap_vs_us >= 0 ? "#22c55e" : "#ef4444"} />
                      ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-3">
            🔴 Retailer cheaper = competitor undercuts us. 🟢 We undercut = headroom to hold/raise.
          </p>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase text-slate-400">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  );
}
