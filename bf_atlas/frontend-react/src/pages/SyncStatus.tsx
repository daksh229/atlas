import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { syncAll, syncSource, getSyncStatus } from "../api/endpoints";
import { useApi } from "../hooks/useApi";
import { ErrorMsg, Loading, PageHeader } from "../components/common";

export function SyncStatus() {
  const [busy, setBusy] = useState(false);
  const { data, loading, error, refetch } = useApi(() => getSyncStatus(), []);

  async function doSync(fn: () => Promise<any>) {
    setBusy(true);
    try {
      await fn();
      refetch();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="🔄 Integration sync status"
        subtitle="Odoo ERP (read-only) and NetHunt CRM (two-way) — POC uses mock clients."
      />

      <div className="flex gap-3 mb-5">
        <button className="btn-ghost border border-slate-200" disabled={busy} onClick={() => doSync(() => syncSource("odoo"))}>
          Sync Odoo
        </button>
        <button className="btn-ghost border border-slate-200" disabled={busy} onClick={() => doSync(() => syncSource("nethunt"))}>
          Sync NetHunt
        </button>
        <button className="btn-primary" disabled={busy} onClick={() => doSync(syncAll)}>
          <RefreshCw size={16} className={busy ? "animate-spin" : ""} /> Sync all
        </button>
      </div>

      {error && <ErrorMsg message={error} />}
      {loading || !data ? (
        <Loading />
      ) : data.length === 0 ? (
        <p className="text-slate-500">No syncs yet — click <strong>Sync all</strong>.</p>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-500 text-xs">
              <tr>
                <th className="px-4 py-2">Source</th><th className="px-4 py-2">Entity</th>
                <th className="px-4 py-2 text-right">Records</th><th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Last synced</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-medium uppercase">{r.source}</td>
                  <td className="px-4 py-2">{r.entity}</td>
                  <td className="px-4 py-2 text-right">{r.records_synced}</td>
                  <td className="px-4 py-2">
                    <span className="badge bg-green-100 text-green-700">{r.status}</span>
                  </td>
                  <td className="px-4 py-2 text-slate-500">{r.synced_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-slate-400 mt-4">
        Phase 1: scheduled Odoo pull every 15 min (Celery beat) + NetHunt webhooks for real-time updates,
        last_modified_at conflict resolution. The FastAPI backend already hosts these endpoints.
      </p>
    </div>
  );
}
