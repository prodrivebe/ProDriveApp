import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { MainLayout } from "../layouts/MainLayout";
import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";
import { OrdersPage } from "../pages/OrdersPage";
import { OrderDetailPage } from "../pages/OrderDetailPage";
import { CreateOrderPage } from "../pages/CreateOrderPage";
import { DriversPage } from "../pages/DriversPage";
import { DriverDetailPage } from "../pages/DriverDetailPage";
import { FleetPage } from "../pages/FleetPage";
import { TruckDetailPage } from "../pages/TruckDetailPage";
import { CustomersPage } from "../pages/CustomersPage";
import { CustomerDetailPage } from "../pages/CustomerDetailPage";
import { DocumentsPage } from "../pages/DocumentsPage";
import { NotificationsPage } from "../pages/NotificationsPage";
import { PlanningBoardPage } from "../pages/PlanningBoardPage";
import { LoadingBoardPage } from "../pages/LoadingBoardPage";
import { SettingsPage } from "../pages/SettingsPage";
import { useAuth } from "../hooks/useAuth";

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/" replace />;
  return children;
}

export function AppRouter() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicOnly>
            <LoginPage />
          </PublicOnly>
        }
      />
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/orders/new" element={<CreateOrderPage />} />
          <Route path="/orders/:orderId" element={<OrderDetailPage />} />
          <Route path="/drivers" element={<DriversPage />} />
          <Route path="/drivers/:driverId" element={<DriverDetailPage />} />
          <Route path="/fleet" element={<FleetPage />} />
          <Route path="/fleet/trucks/:truckId" element={<TruckDetailPage />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="/customers/:customerId" element={<CustomerDetailPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/planning" element={<PlanningBoardPage />} />
          <Route path="/planning/loading/:orderId" element={<LoadingBoardPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
