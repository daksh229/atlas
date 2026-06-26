import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { Onboarding } from "./pages/Onboarding";
import { OpportunityAlerts } from "./pages/OpportunityAlerts";
import { Overview } from "./pages/Overview";
import { BrandsSell, BrandsBuy } from "./pages/BrandMaps";
import { BrandDetail } from "./pages/BrandDetail";
import { MyClients } from "./pages/MyClients";
import { MySuppliers } from "./pages/MySuppliers";
import { OffersInbox } from "./pages/OffersInbox";
import { RetailerRadar } from "./pages/RetailerRadar";
import { BrandCatalog } from "./pages/BrandCatalog";

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
        <Route path="/" element={<OpportunityAlerts />} />
        <Route path="/overview" element={<Overview />} />
        <Route path="/sell" element={<BrandsSell />} />
        <Route path="/buy" element={<BrandsBuy />} />
        <Route path="/brand/:brandId" element={<BrandDetail />} />
        <Route path="/clients" element={<MyClients />} />
        <Route path="/suppliers" element={<MySuppliers />} />
        <Route path="/offers" element={<OffersInbox />} />
        <Route path="/radar" element={<RetailerRadar />} />
        <Route path="/catalog" element={<BrandCatalog />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
