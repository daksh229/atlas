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

export function Pill({ children, tone = "slate" }: { children: React.ReactNode; tone?: string }) {
  const map: Record<string, string> = {
    slate: "bg-slate-100 text-slate-600",
    green: "bg-green-100 text-green-700",
    amber: "bg-amber-100 text-amber-700",
    red: "bg-red-100 text-red-700",
    brand: "bg-brand-50 text-brand-700",
  };
  return <span className={`badge ${map[tone] || map.slate}`}>{children}</span>;
}

export function eur(n: number | null | undefined): string {
  if (n == null) return "—";
  return "€" + Math.round(n).toLocaleString();
}
