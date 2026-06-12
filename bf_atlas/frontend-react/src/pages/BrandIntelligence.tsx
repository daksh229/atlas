import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "../auth/AuthContext";
import { ALL_REGIONS } from "../auth/types";
import { useApi } from "../hooks/useApi";
import { getBrandDetail, getBrandsBuy, getBrandsSell } from "../api/endpoints";
import { DirectionalNote, ErrorMsg, Loading, PageHeader, eur } from "../components/common";

type Tab = "sell" | "buy" | "detail";

export function BrandIntelligence() {
  const { auth } = useAuth();
  const region = auth!.activeRegion;
  const scope = region === ALL_REGIONS ? "all regions" : region;
  const [tab, setTab] = useState<Tab>("sell");

  return (
    <div>
      <PageHeader title="🏷️ Brand Intelligence" subtitle={`Demand vs sourcing per brand · scoped to ${scope}`} />
      <DirectionalNote />

      <div className="flex gap-1 mb-4 border-b border-slate-200">
        {([["sell", "💰 Brands I Can Sell"], ["buy", "🛒 Brands I Can Buy"], ["detail", "🔍 Brand detail"]] as [Tab, string][]).map(
          ([t, label]) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium -mb-px border-b-2 ${
                tab === t ? "border-brand-500 text-brand-700" : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              {label}
            </button>
          )
        )}
      </div>

      {tab === "sell" && <SellTab region={region} />}
      {tab === "buy" && <BuyTab region={region} />}
      {tab === "detail" && <DetailTab region={region} />}
    </div>
  );
}

function SellTab({ region }: { region: string }) {
  const { data, loading, error } = useApi(() => getBrandsSell(region), [region]);
  if (error) return <ErrorMsg message={error} />;
  if (loading || !data) return <Loading />;
  return (
    <div className="card p-4">
      <p className="text-sm text-slate-500 mb-3">Where client demand exists — what you can place.</p>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="brand" fontSize={10} angle={-30} textAnchor="end" height={70} />
          <YAxis fontSize={11} />
          <Tooltip />
          <Bar dataKey="total_wanted" fill="#6c5ce7" radius={[4, 4, 0, 0]} name="Units wanted" />
        </BarChart>
      </ResponsiveContainer>
      <Table rows={data} />
    </div>
  );
}

function BuyTab({ region }: { region: string }) {
  const { data, loading, error } = useApi(() => getBrandsBuy(region), [region]);
  if (error) return <ErrorMsg message={error} />;
  if (loading || !data) return <Loading />;
  return (
    <div className="card p-4">
      <p className="text-sm text-slate-500 mb-3">
        Supplier offers available to source — scoped to your region (managers see all).
      </p>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={[...data].sort((a, b) => a.best_buy_price - b.best_buy_price)} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" fontSize={11} tickFormatter={(v) => `€${v}`} />
          <YAxis type="category" dataKey="brand" width={120} fontSize={10} />
          <Tooltip formatter={(v: number) => eur(v)} />
          <Bar dataKey="best_buy_price" fill="#6c5ce7" radius={[0, 4, 4, 0]} name="Best buy €" />
        </BarChart>
      </ResponsiveContainer>
      <Table rows={data} />
    </div>
  );
}

function DetailTab({ region }: { region: string }) {
  const brands = useApi(() => getBrandsBuy(region), [region]);
  const [brand, setBrand] = useState<string>("");
  const effective = brand || brands.data?.[0]?.brand || "";
  const detail = useApi(
    () => (effective ? getBrandDetail(effective, region) : Promise.resolve(null as any)),
    [effective, region]
  );

  if (brands.loading || !brands.data) return <Loading />;

  return (
    <div className="space-y-4">
      <select
        className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        value={effective}
        onChange={(e) => setBrand(e.target.value)}
      >
        {brands.data.map((b) => (
          <option key={b.brand} value={b.brand}>{b.brand}</option>
        ))}
      </select>

      {detail.loading || !detail.data ? (
        <Loading />
      ) : (
        <>
          {detail.data.best ? (
            <div className="rounded-lg bg-green-50 border border-green-200 text-green-800 px-4 py-3 text-sm">
              <strong>Closed-loop opportunity:</strong> buy {effective} @ {eur(detail.data.best.buy)} → sell @{" "}
              {eur(detail.data.best.sell)} · <strong>{eur(detail.data.best.margin_per_unit)}/unit margin</strong>
            </div>
          ) : (
            <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 text-sm">
              No profitable buy→sell loop for this brand in scope.
            </div>
          )}
          <div className="grid lg:grid-cols-2 gap-4">
            <div className="card p-4">
              <h4 className="font-semibold mb-2">🛒 Supplier offers</h4>
              <Table rows={detail.data.offers} />
            </div>
            <div className="card p-4">
              <h4 className="font-semibold mb-2">💰 Client demand</h4>
              <Table rows={detail.data.demands} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Table({ rows }: { rows: any[] }) {
  if (!rows?.length) return <p className="text-slate-400 text-sm py-3">No rows.</p>;
  const cols = Object.keys(rows[0]);
  return (
    <div className="overflow-auto max-h-80 mt-3 border border-slate-100 rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-500 text-xs sticky top-0">
          <tr>{cols.map((c) => <th key={c} className="px-3 py-2">{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.slice(0, 50).map((r, i) => (
            <tr key={i} className="border-t border-slate-100">
              {cols.map((c) => <td key={c} className="px-3 py-1.5">{String(r[c])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
