import { Loader2, AlertTriangle } from "lucide-react";

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 py-10 justify-center">
      <Loader2 className="animate-spin" size={18} /> {label}
    </div>
  );
}

export function ErrorMsg({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg bg-red-50 text-red-700 border border-red-200 p-3 text-sm">
      <AlertTriangle size={18} className="mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-5">
      <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
      {subtitle && <p className="text-slate-500 text-sm mt-1">{subtitle}</p>}
    </div>
  );
}

export function DirectionalNote() {
  return (
    <div className="mb-5 rounded-lg bg-brand-50 border border-brand-100 text-brand-900 text-sm px-4 py-2.5">
      🧭 <strong>Directional proof</strong> — built from the public brief on mock data.
      Exact rules/layout would conform to BF's spec under NDA.
    </div>
  );
}

export function eur(n: number | null | undefined): string {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString();
}
