import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, User } from "lucide-react";
import { getTraders } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import type { Trader } from "../auth/types";

export function Onboarding() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [traders, setTraders] = useState<Trader[]>([]);
  const [picked, setPicked] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    setError(null);
    getTraders()
      .then((t) => {
        setTraders(t);
        if (t.length === 0) setError("No traders returned — is the database built? (data/pipeline/build.py)");
      })
      .catch(() =>
        setError(
          "Cannot reach the backend. Start it: `cd bf_atlas/backend` → " +
            "`uvicorn app.main:app --port 8000`, then retry."
        )
      )
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function finish() {
    if (!picked) return;
    setBusy(true);
    setError(null);
    try {
      await login(picked);
      navigate("/");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Could not start session.");
      setBusy(false);
    }
  }

  const byTeam = traders.reduce<Record<string, Trader[]>>((acc, t) => {
    (acc[t.team] ??= []).push(t);
    return acc;
  }, {});

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-900 to-brand-700 p-4">
      <div className="w-full max-w-lg card p-8">
        <div className="text-center mb-6">
          <div className="text-2xl font-bold text-brand-700">BF Atlas</div>
          <p className="text-slate-500 text-sm mt-1">
            Sign in as a trader — you'll see only your own clients, suppliers and alerts.
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 text-red-700 border border-red-200 p-3 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center gap-2 text-slate-500 py-8 justify-center">
            <Loader2 className="animate-spin" size={18} /> Loading traders…
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(byTeam).map(([team, members]) => (
              <div key={team}>
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">
                  Team {team}
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {members.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setPicked(t.id)}
                      className={`flex items-center gap-3 rounded-lg border px-3 py-3 text-sm font-medium transition text-left ${
                        picked === t.id
                          ? "border-brand-500 bg-brand-50 text-brand-700"
                          : "border-slate-200 hover:border-brand-300"
                      }`}
                    >
                      <User size={16} className="text-brand-500" /> {t.name}
                    </button>
                  ))}
                </div>
              </div>
            ))}
            <button
              className="btn-primary w-full justify-center"
              disabled={!picked || busy}
              onClick={finish}
            >
              {busy ? <Loader2 className="animate-spin" size={16} /> : null}
              Enter Atlas
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
