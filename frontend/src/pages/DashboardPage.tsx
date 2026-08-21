import { Link as RouterLink } from "react-router-dom";
import {
  Box,
  Button,
  Stack,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "../services/documentsService";
import { notificationsService } from "../services/notificationsService";
import { ordersService } from "../services/ordersService";
import { ErrorAlert } from "../components/ErrorAlert";
import { DashboardEmptyState, DashboardSkeleton } from "../components/DashboardSkeleton";
import { OperationsBoard } from "../components/OperationsBoard";
import type { KpiDashboard, Notification, OrdersReport, OrderSummary } from "../types/api";
import { PageHeader, PremiumCard, StatTile } from "../design-system";
import { isToday } from "../utils/format";

function FleetSnapshot({ fleet }: { fleet: KpiDashboard["fleet"] }) {
  return (
    <PremiumCard title="Fleet snapshot">
      <Typography>Drivers: {fleet.drivers.active}/{fleet.drivers.total} active</Typography>
      <Typography>Trucks: {fleet.trucks.active}/{fleet.trucks.total} active</Typography>
      <Typography>Trailers: {fleet.trailers.active}/{fleet.trailers.total} active</Typography>
    </PremiumCard>
  );
}

function buildDashboardMetrics(
  kpi: KpiDashboard,
  ordersReport: OrdersReport,
  orders: OrderSummary[],
) {
  const byStatus = ordersReport.by_status ?? {};
  return {
    waitingAssignment: (byStatus.READY ?? 0) + (byStatus.DRAFT ?? 0) + (byStatus.ASSIGNED ?? 0),
    loadingOrders:
      (byStatus.LOADING ?? 0) + (byStatus.LOADED ?? 0) + (byStatus.ARRIVED_PICKUP ?? 0),
    inTransit:
      (byStatus.IN_TRANSIT ?? 0) + (byStatus.ARRIVED_DELIVERY ?? 0) + (byStatus.DELIVERING ?? 0),
    completedToday: orders.filter(
      (order) => order.status === "COMPLETED" && isToday(order.updated_at),
    ).length,
    delayedOrders: orders.filter(
      (order) =>
        !["COMPLETED", "CANCELLED"].includes(order.status) &&
        order.planned_delivery_date &&
        new Date(order.planned_delivery_date) < new Date(),
    ).length,
  };
}

export function DashboardPage() {
  const dashboardQuery = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const [kpi, ordersReport, notifications, orders] = await Promise.all([
        dashboardService.kpi(),
        dashboardService.ordersReport(),
        notificationsService.list(true),
        ordersService.list({ page: 1, page_size: 100 }),
      ]);
      return { kpi, ordersReport, notifications, orders };
    },
  });

  if (dashboardQuery.isLoading) {
    return <DashboardSkeleton />;
  }

  if (dashboardQuery.isError) {
    return <ErrorAlert error={dashboardQuery.error} />;
  }

  const data = dashboardQuery.data;
  if (!data) {
    return <ErrorAlert error={new Error("Dashboard data is unavailable.")} />;
  }

  const { kpi, ordersReport, notifications, orders } = data;
  const orderItems = orders?.items ?? [];
  const unreadNotifications = notifications ?? [];
  const metrics = buildDashboardMetrics(kpi, ordersReport, orderItems);
  const hasActivity =
    kpi.total_orders > 0 ||
    orderItems.length > 0 ||
    kpi.fleet.drivers.total > 0 ||
    kpi.fleet.trucks.total > 0 ||
    kpi.fleet.trailers.total > 0;

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Operations Board"
        subtitle="Live transport overview — updates automatically"
        actions={
          <Button component={RouterLink} to="/orders/new" variant="contained">
            Create order
          </Button>
        }
      />

      {!hasActivity ? <DashboardEmptyState /> : null}

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatTile label="Waiting assignment" value={metrics.waitingAssignment} accent />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatTile label="Active orders" value={kpi.active_orders} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatTile label="Loading" value={metrics.loadingOrders} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatTile label="In transit" value={metrics.inTransit} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatTile label="Delayed" value={metrics.delayedOrders} hint="Past planned delivery" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatTile label="Completed today" value={metrics.completedToday} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatTile label="Unread alerts" value={unreadNotifications.length} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatTile label="Active drivers" value={kpi.active_drivers} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <FleetSnapshot fleet={kpi.fleet} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <PremiumCard title="Recent alerts">
            {unreadNotifications.length === 0 ? (
              <Typography color="text.secondary">No unread alerts.</Typography>
            ) : (
              unreadNotifications.slice(0, 5).map((item: Notification) => (
                <Box key={item.id} sx={{ mb: 1.5 }}>
                  <Typography fontWeight={600}>{item.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {item.message}
                  </Typography>
                </Box>
              ))
            )}
          </PremiumCard>
        </Grid>
      </Grid>

      <OperationsBoard />
    </Stack>
  );
}
