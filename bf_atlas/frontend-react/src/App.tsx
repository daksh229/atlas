import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { Onboarding } from "./pages/Onboarding";
import { Dashboard } from "./pages/Dashboard";
import { AskAtlas } from "./pages/AskAtlas";
import { OpportunityAlerts } from "./pages/OpportunityAlerts";
import { BrandIntelligence } from "./pages/BrandIntelligence";
import { PriceList } from "./pages/PriceList";
import { RetailerRadar } from "./pages/RetailerRadar";
import { SyncStatus } from "./pages/SyncStatus";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { auth } = useAuth();
  return auth ? children : <Navigate to="/onboarding" replace />;
}

export default function App() {
  const { auth } = useAuth();
  return (
    <Routes>
      <Route
        path="/onboarding"
        element={auth ? <Navigate to="/" replace /> : <Onboarding />}
      />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/ask" element={<AskAtlas />} />
        <Route path="/alerts" element={<OpportunityAlerts />} />
        <Route path="/brands" element={<BrandIntelligence />} />
        <Route path="/pricelist" element={<PriceList />} />
        <Route path="/radar" element={<RetailerRadar />} />
        <Route path="/sync" element={<SyncStatus />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
