import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { useApi } from "../hooks/useApi";
import { getBrandDetail } from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, Pill, eur } from "../components/common";

export function BrandDetail() {
  const { brandId } = useParams();
  const navigate = useNavigate();
  const { data, loading, error } = useApi(() => getBrandDetail(brandId!), [brandId]);

  if (error) return <ErrorMsg message={error} />;
  if (loading || !data) return <Loading />;

  return (
    <div>
      <button className="btn-ghost mb-3" onClick={() => navigate(-1)}>
        <ArrowLeft size={16} /> Back
      </button>
      <PageHeader
        title={`🏷️ ${data.brand}`}
        subtitle={`${data.category} · best historical sell price ${eur(
          data.best_historical_sell_price
        )} · clients & suppliers you don't own are hidden`}
      />

      <div className="grid lg:grid-cols-2 gap-4">
        <Card title="👥 Colleagues active on this brand">
          <SimpleTable
            rows={data.colleagues}
            cols={["colleague", "team", "demand_signals", "supply_signals"]}
          />
        </Card>

        <Card title="🛰️ Retailers carrying it">
          <SimpleTable
            rows={data.retailers}
            cols={["retailer", "product_name", "price", "stock_status"]}
            fmt={{ price: eur }}
          />
        </Card>

        <Card title="💰 Clients wanting it">
          {data.demands.length === 0 ? (
            <Empty />
          ) : (
            <ul className="text-sm divide-y divide-slate-100">
              {data.demands.map((d, i) => (
                <li key={i} className="py-2 flex items-center justify-between gap-2">
                  <span>
                    {d.mine ? (
                      <Pill tone="brand">yours</Pill>
                    ) : (
                      <Pill tone="slate">masked</Pill>
                    )}{" "}
                    {d.client}
                  </span>
                  <span className="text-slate-500">
                    {eur(d.target_price)} · {d.wanted_qty} units
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="📦 Supply available">
          {data.offers.length === 0 ? (
            <Empty />
          ) : (
            <ul className="text-sm divide-y divide-slate-100">
              {data.offers.map((o, i) => (
                <li key={i} className="py-2 flex items-center justify-between gap-2">
                  <span>
                    {o.mine ? (
                      <Pill tone="brand">yours</Pill>
                    ) : (
                      <Pill tone="slate">masked</Pill>
                    )}{" "}
                    {o.supplier}
                  </span>
                  <span className="text-slate-500">
                    {eur(o.offer_price)} · {o.available_qty} units
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-4">
      <h3 className="font-semibold text-slate-700 mb-2">{title}</h3>
      {children}
    </div>
  );
}
function Empty() {
  return <p className="text-slate-400 text-sm py-3">None.</p>;
}
function SimpleTable({
  rows,
  cols,
  fmt = {},
}: {
  rows: any[];
  cols: string[];
  fmt?: Record<string, (v: any) => string>;
}) {
  if (!rows?.length) return <Empty />;
  return (
    <div className="overflow-auto max-h-72">
      <table className="w-full text-sm">
        <thead className="text-left text-slate-400 text-xs">
          <tr>
            {cols.map((c) => (
              <th key={c} className="py-1 pr-3">
                {c.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-slate-100">
              {cols.map((c) => (
                <td key={c} className="py-1.5 pr-3">
                  {fmt[c] ? fmt[c](r[c]) : String(r[c] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
