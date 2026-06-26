import { useState } from "react";
import { Mail, Sparkles, Send, Check, Loader2 } from "lucide-react";
import { useApi } from "../hooks/useApi";
import {
  getInbox,
  getEmail,
  parseEmail,
  acceptOffers,
  getOffers,
  submitOffer,
} from "../api/endpoints";
import { ErrorMsg, Loading, PageHeader, Pill, eur } from "../components/common";

export function OffersInbox() {
  const inbox = useApi(() => getInbox(), []);
  const recorded = useApi(() => getOffers(), []);
  const [selected, setSelected] = useState<string | null>(null);
  const [body, setBody] = useState<string>("");
  const [engine, setEngine] = useState<string | null>(null);
  const [rows, setRows] = useState<any[] | null>(null);
  const [parsing, setParsing] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [result, setResult] = useState<any>(null);

  async function open(id: string) {
    setSelected(id);
    setRows(null);
    setResult(null);
    setEngine(null);
    const e = await getEmail(id);
    setBody(e.body);
  }

  async function runParse() {
    if (!selected) return;
    setParsing(true);
    setResult(null);
    try {
      const p = await parseEmail(selected);
      setEngine(p.engine);
      setRows(p.offers);
    } finally {
      setParsing(false);
    }
  }

  function edit(i: number, key: string, val: any) {
    setRows((rs) => rs!.map((r, idx) => (idx === i ? { ...r, [key]: val } : r)));
  }

  async function accept() {
    if (!rows) return;
    setAccepting(true);
    try {
      const usable = rows.filter((r) => !r.unknown_brand);
      const res = await acceptOffers(usable);
      setResult(res);
      recorded.refetch();
    } finally {
      setAccepting(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="✉️ Offers Inbox"
        subtitle="Open a supplier email → AI extracts the offers → review → accept. Matched client demand fires an Offer-to-Request alert."
      />

      {inbox.error && <ErrorMsg message={inbox.error} />}
      {inbox.loading || !inbox.data ? (
        <Loading />
      ) : (
        <div className="grid lg:grid-cols-2 gap-4">
          {/* Inbox list */}
          <div className="card p-3">
            <h3 className="font-semibold text-slate-700 mb-2 px-1">Supplier emails</h3>
            <ul className="divide-y divide-slate-100">
              {inbox.data.map((e) => (
                <li key={e.id}>
                  <button
                    onClick={() => open(e.id)}
                    className={`w-full text-left px-2 py-2.5 rounded-lg ${
                      selected === e.id ? "bg-brand-50" : "hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Mail size={14} className="text-slate-400" />
                      <span className="font-medium text-sm">{e.subject}</span>
                    </div>
                    <div className="text-xs text-slate-400 pl-6">{e.from}</div>
                    <div className="text-xs text-slate-500 pl-6 truncate">{e.preview}</div>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Reading pane + extraction */}
          <div className="card p-4">
            {!selected ? (
              <p className="text-slate-400 text-sm py-10 text-center">
                Select an email to extract its offers.
              </p>
            ) : (
              <>
                <pre className="text-xs bg-slate-50 border border-slate-100 rounded-lg p-3 whitespace-pre-wrap max-h-44 overflow-auto">
                  {body}
                </pre>
                <button className="btn-primary mt-3" disabled={parsing} onClick={runParse}>
                  {parsing ? <Loader2 className="animate-spin" size={15} /> : <Sparkles size={15} />}
                  {parsing ? "Extracting…" : "Extract offers"}
                </button>

                {rows && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-slate-700">
                        Extracted offers{" "}
                        <span className="text-slate-400 font-normal">({rows.length})</span>
                      </h4>
                      {engine && (
                        <Pill tone={engine === "ai" ? "brand" : "slate"}>
                          {engine === "ai" ? "AI extracted" : "heuristic"}
                        </Pill>
                      )}
                    </div>

                    {rows.length === 0 ? (
                      <p className="text-slate-400 text-sm py-3">No offers found in this email.</p>
                    ) : (
                      <div className="space-y-2">
                        {rows.map((r, i) => (
                          <div
                            key={i}
                            className={`rounded-lg border p-2 text-sm ${
                              r.unknown_brand
                                ? "border-amber-200 bg-amber-50"
                                : "border-slate-200"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-medium">
                                {r.brand || r.brand_surface}{" "}
                                {r.unknown_brand ? (
                                  <Pill tone="amber">unknown brand — won't match</Pill>
                                ) : r.brand_surface !== r.brand ? (
                                  <span className="text-slate-400 text-xs">
                                    (from “{r.brand_surface}”)
                                  </span>
                                ) : null}
                              </span>
                              <span className="text-xs text-slate-400">
                                conf {Math.round((r.confidence ?? 0) * 100)}%
                              </span>
                            </div>
                            <div className="flex gap-2 mt-1">
                              <label className="text-xs text-slate-500">
                                €/unit
                                <input
                                  className="ml-1 w-20 rounded border border-slate-300 px-1 py-0.5"
                                  type="number"
                                  value={r.offer_price ?? ""}
                                  onChange={(e) => edit(i, "offer_price", Number(e.target.value))}
                                />
                              </label>
                              <label className="text-xs text-slate-500">
                                qty
                                <input
                                  className="ml-1 w-20 rounded border border-slate-300 px-1 py-0.5"
                                  type="number"
                                  value={r.quantity ?? ""}
                                  onChange={(e) => edit(i, "quantity", Number(e.target.value))}
                                />
                              </label>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {rows.some((r) => !r.unknown_brand) && (
                      <button className="btn-primary mt-3" disabled={accepting} onClick={accept}>
                        {accepting ? <Loader2 className="animate-spin" size={15} /> : <Check size={15} />}
                        Accept &amp; match
                      </button>
                    )}

                    {result && (
                      <div
                        className={`mt-3 rounded-lg px-4 py-3 text-sm border ${
                          result.match_count > 0
                            ? "bg-green-50 border-green-200 text-green-800"
                            : "bg-slate-50 border-slate-200 text-slate-600"
                        }`}
                      >
                        Recorded {result.accepted} offer(s)
                        {result.skipped ? `, skipped ${result.skipped}` : ""}.{" "}
                        {result.match_count > 0 ? (
                          <>
                            <strong>{result.match_count} Offer-to-Request match(es)</strong> —{" "}
                            {result.matches
                              .slice(0, 4)
                              .map((m: any) => `${m.brand}: ${eur(m.margin_value)}`)
                              .join(", ")}
                            . Relevant traders notified.
                          </>
                        ) : (
                          "No matching client demand right now."
                        )}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Quick add + recorded list */}
      <QuickAdd onAdded={() => recorded.refetch()} />
      <h3 className="font-semibold text-slate-700 mt-6 mb-2">Recorded offers</h3>
      {recorded.loading || !recorded.data ? (
        <Loading />
      ) : !recorded.data.length ? (
        <div className="card p-6 text-center text-slate-500">No offers recorded yet.</div>
      ) : (
        <div className="card p-4 overflow-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-slate-400 text-xs">
              <tr>
                <th className="py-2">Brand</th>
                <th className="text-right">€/unit</th>
                <th className="text-right">Qty</th>
                <th>Source</th>
                <th>By</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {recorded.data.map((o, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="py-2 font-medium">{o.brand}</td>
                  <td className="text-right">{eur(o.offer_price)}</td>
                  <td className="text-right">{o.available_qty}</td>
                  <td>
                    <Pill tone={o.source === "email_offer" ? "brand" : "slate"}>
                      {o.source === "email_offer" ? "email" : "manual"}
                    </Pill>
                  </td>
                  <td className="text-slate-500">{o.submitted_by}</td>
                  <td className="text-slate-500">{o.fired_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function QuickAdd({ onAdded }: { onAdded: () => void }) {
  const [brand, setBrand] = useState("");
  const [price, setPrice] = useState("");
  const [qty, setQty] = useState("");
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<any>(null);

  async function send() {
    if (!brand || !price || !qty) return;
    setBusy(true);
    setRes(null);
    try {
      const r = await submitOffer(brand, Number(price), Number(qty));
      setRes(r);
      if (r.ok) onAdded();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card p-4 mt-6">
      <h3 className="font-semibold text-slate-700 mb-3">Quick-add an offer (no email)</h3>
      <div className="grid sm:grid-cols-4 gap-3">
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder="Brand (e.g. YSL)"
          value={brand}
          onChange={(e) => setBrand(e.target.value)}
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder="€/unit"
          type="number"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder="Qty"
          type="number"
          value={qty}
          onChange={(e) => setQty(e.target.value)}
        />
        <button className="btn-primary justify-center" disabled={busy} onClick={send}>
          <Send size={15} /> Submit
        </button>
      </div>
      {res && (
        <div
          className={`mt-3 rounded-lg px-4 py-2.5 text-sm border ${
            !res.ok
              ? "bg-amber-50 border-amber-200 text-amber-800"
              : res.match_count > 0
              ? "bg-green-50 border-green-200 text-green-800"
              : "bg-slate-50 border-slate-200 text-slate-600"
          }`}
        >
          {!res.ok
            ? res.error
            : res.match_count > 0
            ? `Offer-to-Request Match! ${res.brand} matched ${res.match_count} client request(s).`
            : `Offer recorded for ${res.brand}. No matching demand right now.`}
        </div>
      )}
    </div>
  );
}
