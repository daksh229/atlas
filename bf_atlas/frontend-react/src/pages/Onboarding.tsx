import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Briefcase, UserCog, ArrowRight, ArrowLeft, Loader2 } from "lucide-react";
import { fetchRegions } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../auth/types";

export function Onboarding() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2>(1);
  const [role, setRole] = useState<Role | null>(null);
  const [regions, setRegions] = useState<string[]>([]);
  const [region, setRegion] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingRegions, setLoadingRegions] = useState(true);

  function loadRegions() {
    setLoadingRegions(true);
    setError(null);
    fetchRegions()
      .then((r) => {
        setRegions(r);
        if (r.length === 0)
          setError("The backend returned no regions — is the database initialised?");
      })
      .catch(() =>
        setError(
          "Cannot reach the backend API. Start it first: `cd bf_atlas/backend` → " +
            "`uvicorn app.main:app --port 8000`, then retry."
        )
      )
      .finally(() => setLoadingRegions(false));
  }

  useEffect(loadRegions, []);

  function pickRole(r: Role) {
    setRole(r);
    setStep(2);
  }

  async function finish() {
    if (!role || !region) return;
    setBusy(true);
    setError(null);
    try {
      await login(role, region);
      navigate("/");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Could not start session.");
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-900 to-brand-700 p-4">
      <div className="w-full max-w-lg card p-8">
        <div className="text-center mb-6">
          <div className="text-2xl font-bold text-brand-700">BF Atlas</div>
          <p className="text-slate-500 text-sm mt-1">Trader Intelligence Platform</p>
        </div>

        {/* progress */}
        <div className="flex items-center justify-center gap-2 mb-8 text-xs">
          <span className={step >= 1 ? "text-brand-600 font-semibold" : "text-slate-400"}>
            1 · Role
          </span>
          <div className="w-8 h-px bg-slate-200" />
          <span className={step >= 2 ? "text-brand-600 font-semibold" : "text-slate-400"}>
            2 · Region
          </span>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 text-red-700 border border-red-200 p-3 text-sm">
            {error}
          </div>
        )}

        {step === 1 && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600 mb-2">How are you signing in?</p>
            <button
              className="w-full card p-4 text-left hover:border-brand-400 hover:bg-brand-50 transition flex items-center gap-4"
              onClick={() => pickRole("trader")}
            >
              <Briefcase className="text-brand-600" />
              <div>
                <div className="font-semibold">Trader</div>
                <div className="text-xs text-slate-500">
                  See only your allotted region's data.
                </div>
              </div>
              <ArrowRight className="ml-auto text-slate-300" size={18} />
            </button>
            <button
              className="w-full card p-4 text-left hover:border-brand-400 hover:bg-brand-50 transition flex items-center gap-4"
              onClick={() => pickRole("manager")}
            >
              <UserCog className="text-brand-600" />
              <div>
                <div className="font-semibold">Manager</div>
                <div className="text-xs text-slate-500">
                  Cross-region view; switch between all regions.
                </div>
              </div>
              <ArrowRight className="ml-auto text-slate-300" size={18} />
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              {role === "trader"
                ? "Select your allotted region. You'll only be able to access this region."
                : "Select your home region (you can switch to any region or the cross-region view later)."}
            </p>
            {loadingRegions ? (
              <div className="flex items-center gap-2 text-slate-500 py-6 justify-center">
                <Loader2 className="animate-spin" size={18} /> Loading regions…
              </div>
            ) : regions.length === 0 ? (
              <button className="btn-ghost border border-slate-200" onClick={loadRegions}>
                Retry
              </button>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {regions.map((r) => (
                  <button
                    key={r}
                    onClick={() => setRegion(r)}
                    className={`rounded-lg border px-3 py-3 text-sm font-medium transition ${
                      region === r
                        ? "border-brand-500 bg-brand-50 text-brand-700"
                        : "border-slate-200 hover:border-brand-300"
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            )}
            <div className="flex items-center justify-between pt-2">
              <button className="btn-ghost" onClick={() => setStep(1)}>
                <ArrowLeft size={16} /> Back
              </button>
              <button className="btn-primary" disabled={!region || busy} onClick={finish}>
                {busy ? <Loader2 className="animate-spin" size={16} /> : null}
                Enter Atlas
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
