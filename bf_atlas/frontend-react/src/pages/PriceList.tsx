import { useState } from "react";
import { Loader2, Upload } from "lucide-react";
import { analyzePricelist } from "../api/endpoints";
import { DirectionalNote, PageHeader, eur } from "../components/common";

type Result = Awaited<ReturnType<typeof analyzePricelist>>;

export function PriceList() {
  const [useSample, setUseSample] = useState(true);
  const [preferAi, setPreferAi] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const res = await analyzePricelist({
        file: useSample ? undefined : file || undefined,
        useSample,
        preferAi,
      });
      setResult(res);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Analysis failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="📑 Price-List Analysis"
        subtitle="Match a messy supplier price list to our catalogue and score the margin."
      />
      <DirectionalNote />

      <div className="card p-4 space-y-4">
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input type="radio" checked={useSample} onChange={() => setUseSample(true)} /> Use sample messy list
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="radio" checked={!useSample} onChange={() => setUseSample(false)} /> Upload CSV
          </label>
          {!useSample && (
            <label className="btn-ghost cursor-pointer">
              <Upload size={16} /> {file ? file.name : "Choose file"}
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>
          )}
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={preferAi} onChange={(e) => setPreferAi(e.target.checked)} />
          Use Claude (AI) matching — off, or no API key, falls back to offline matcher
        </label>
        <button className="btn-primary" onClick={run} disabled={busy || (!useSample && !file)}>
          {busy && <Loader2 className="animate-spin" size={16} />} Analyse price list
        </button>
        {error && <div className="text-red-600 text-sm">{error}</div>}
      </div>

      {result && (
        <div className="mt-4 space-y-4">
          <p className="text-sm text-slate-500">
            Engine: <strong>{result.engine}</strong>
          </p>
          <div className="grid grid-cols-3 gap-4">
            <Stat label="Matched" value={`${result.matched}/${result.total}`} />
            <Stat label="Unmatched" value={result.total - result.matched} />
            <Stat label="Below our cost" value={result.below_cost} />
          </div>
          <div className="card overflow-auto max-h-[28rem]">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-slate-500 text-xs sticky top-0">
                <tr>
                  <th className="px-3 py-2">Supplier line</th>
                  <th className="px-3 py-2">Matched</th>
                  <th className="px-3 py-2 text-right">Conf.</th>
                  <th className="px-3 py-2 text-right">Offered</th>
                  <th className="px-3 py-2 text-right">Our list</th>
                  <th className="px-3 py-2">Signal</th>
                </tr>
              </thead>
              <tbody>
                {result.items.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-3 py-1.5 text-slate-500">{r.supplier_item}</td>
                    <td className="px-3 py-1.5 font-medium">{r.matched || "—"}</td>
                    <td className="px-3 py-1.5 text-right">{r.confidence}</td>
                    <td className="px-3 py-1.5 text-right">{eur(r.offered)}</td>
                    <td className="px-3 py-1.5 text-right">{r.our_price != null ? eur(r.our_price) : "—"}</td>
                    <td className="px-3 py-1.5">{r.flag}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-400">
            Low-confidence / unknown lines are flagged rather than force-matched — the guardrail we'd use on
            AI-parsed supplier emails.
          </p>
        </div>
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
