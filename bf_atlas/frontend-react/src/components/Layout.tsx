import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Siren,
  Tags,
  ShoppingCart,
  Users,
  Truck,
  Inbox,
  FlaskConical,
  Radar,
  BookOpen,
  LayoutDashboard,
  LogOut,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";

// Navigation mirrors the spec's §8 menu sections exactly.
const SECTIONS: {
  section: string;
  items: { to: string; label: string; icon: any; end?: boolean }[];
}[] = [
  {
    section: "My View",
    items: [
      { to: "/", label: "Opportunity Alerts", icon: Siren, end: true },
      { to: "/overview", label: "Overview", icon: LayoutDashboard },
    ],
  },
  {
    section: "Brand Maps",
    items: [
      { to: "/sell", label: "Brands I Can Sell", icon: Tags },
      { to: "/buy", label: "Brands I Can Buy", icon: ShoppingCart },
    ],
  },
  {
    section: "My Relationships",
    items: [
      { to: "/clients", label: "My Clients", icon: Users },
      { to: "/suppliers", label: "My Suppliers", icon: Truck },
    ],
  },
  {
    section: "Market Activity",
    items: [
      { to: "/offers", label: "Offers Inbox", icon: Inbox },
      { to: "/offer-evaluation", label: "Offer Evaluation", icon: FlaskConical },
      { to: "/radar", label: "Retailer Radar", icon: Radar },
    ],
  },
  {
    section: "System",
    items: [{ to: "/catalog", label: "Brand Catalog", icon: BookOpen }],
  },
];

export function Layout() {
  const { auth, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 bg-brand-900 text-white flex flex-col">
        <div className="px-5 py-5 border-b border-white/10">
          <div className="text-lg font-bold">BF Atlas</div>
          <div className="text-xs text-brand-100/70">Trader Intelligence</div>
        </div>
        <nav className="flex-1 p-3 space-y-4 overflow-auto">
          {SECTIONS.map(({ section, items }) => (
            <div key={section}>
              <div className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-wider text-brand-100/40">
                {section}
              </div>
              <div className="space-y-0.5">
                {items.map(({ to, label, icon: Icon, end }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={end}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? "bg-white/15 font-medium"
                          : "text-brand-100/80 hover:bg-white/10"
                      }`
                    }
                  >
                    <Icon size={17} /> {label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
        <div className="p-4 text-xs text-brand-100/60 border-t border-white/10">
          Trader-owned access · real Odoo-export data
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <div className="text-sm text-slate-500">
            Signed in as{" "}
            <span className="font-semibold text-slate-800">{auth?.name}</span>{" "}
            <span className="badge bg-slate-100 text-slate-500 ml-1">
              {auth?.team}
            </span>
          </div>
          <button
            className="btn-ghost"
            onClick={() => {
              logout();
              navigate("/onboarding");
            }}
          >
            <LogOut size={16} /> Exit
          </button>
        </header>
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
