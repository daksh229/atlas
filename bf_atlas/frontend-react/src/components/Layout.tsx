import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquareText,
  Siren,
  Tags,
  FileSpreadsheet,
  Radar,
  RefreshCw,
  Lock,
  LogOut,
  Globe,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { ALL_REGIONS } from "../auth/types";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/ask", label: "Ask Atlas", icon: MessageSquareText },
  { to: "/alerts", label: "Opportunity Alerts", icon: Siren },
  { to: "/brands", label: "Brand Intelligence", icon: Tags },
  { to: "/pricelist", label: "Price-List", icon: FileSpreadsheet },
  { to: "/radar", label: "Retailer Radar", icon: Radar },
  { to: "/sync", label: "Sync Status", icon: RefreshCw },
];

function RegionSwitcher() {
  const { auth, setActiveRegion } = useAuth();
  if (!auth) return null;

  if (auth.role === "trader") {
    return (
      <span className="badge bg-slate-100 text-slate-600 gap-1">
        <Lock size={12} /> {auth.region}
      </span>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <Globe size={16} className="text-slate-400" />
      <select
        className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm"
        value={auth.activeRegion}
        onChange={(e) => setActiveRegion(e.target.value)}
      >
        {auth.allowed_regions.map((r) => (
          <option key={r} value={r}>
            {r === ALL_REGIONS ? "🌍 All regions" : r}
          </option>
        ))}
      </select>
    </div>
  );
}

export function Layout() {
  const { auth, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 bg-brand-900 text-white flex flex-col">
        <div className="px-5 py-5 border-b border-white/10">
          <div className="text-lg font-bold">BF Atlas</div>
          <div className="text-xs text-brand-100/70">Trader Intelligence</div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive ? "bg-white/15 font-medium" : "text-brand-100/80 hover:bg-white/10"
                }`
              }
            >
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 text-xs text-brand-100/60 border-t border-white/10">
          Mock data · directional POC
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <RegionSwitcher />
          <div className="flex items-center gap-3">
            <span className="badge bg-brand-50 text-brand-700 capitalize">
              {auth?.role}
            </span>
            <button
              className="btn-ghost"
              onClick={() => {
                logout();
                navigate("/onboarding");
              }}
            >
              <LogOut size={16} /> Exit
            </button>
          </div>
        </header>
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
