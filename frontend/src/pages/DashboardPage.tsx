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
import { driversService } from "../services/driversService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { OperationsBoard } from "../components/OperationsBoard";
import { isToday } from "../utils/format";

function StatCard({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <Box sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 2, height: "100%" }}>
      <Typography color="text.secondary" variant="body2">
        {label}
      </Typography>
      <Typography variant="h4" fontWeight={700}>
        {value}
      </Typography>
      {hint ? (
        <Typography variant="caption" color="text.secondary">
          {hint}
        </Typography>
      ) : null}
    </Box>
  );
}

export function DashboardPage() {
  const dashboardQuery = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const [kpi, ordersReport, notifications, orders, drivers] = await Promise.all([
        dashboardService.kpi(),
        dashboardService.ordersReport(),
        notificationsService.list(true),
        ordersService.list({ page: 1, page_size: 100 }),
        driversService.list({ page: 1, page_size: 100 }),
      ]);
      return { kpi, ordersReport, notifications, orders, drivers };
    },
  });

  if (dashboardQuery.isLoading) return <LoadingState label="Loading operations board..." />;
  if (dashboardQuery.isError) return <ErrorAlert error={dashboardQuery.error} />;

  const { kpi, ordersReport, notifications, orders, drivers } = dashboardQuery.data;
  const byStatus = ordersReport.by_status;
  const waitingAssignment = (byStatus.READY ?? 0) + (byStatus.DRAFT ?? 0) + (byStatus.ASSIGNED ?? 0);
  const loadingOrders = (byStatus.LOADING ?? 0) + (byStatus.LOADED ?? 0) + (byStatus.ARRIVED_PICKUP ?? 0);
  const inTransit = (byStatus.IN_TRANSIT ?? 0) + (byStatus.ARRIVED_DELIVERY ?? 0) + (byStatus.DELIVERING ?? 0);
  const completedToday = orders.items.filter(
    (order) => order.status === "COMPLETED" && isToday(order.updated_at),
  ).length;
  const delayedOrders = orders.items.filter(
    (order) =>
      !["COMPLETED", "CANCELLED"].includes(order.status) &&
      order.planned_delivery_date &&
      new Date(order.planned_delivery_date) < new Date(),
  ).length;

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 2, flexWrap: "wrap" }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Operations Board
          </Typography>
          <Typography color="text.secondary">
            Live transport overview — updates automatically
          </Typography>
        </Box>
        <Button component={RouterLink} to="/orders/new" variant="contained">
          Create order
        </Button>
      </Box>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Waiting assignment" value={waitingAssignment} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Active orders" value={kpi.active_orders} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Loading" value={loadingOrders} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="In transit" value={inTransit} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Delayed" value={delayedOrders} hint="Past planned delivery" /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Completed today" value={completedToday} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Unread alerts" value={notifications.length} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Active drivers" value={drivers.items.filter((d) => d.active).length} /></Grid>
      </Grid>

      <OperationsBoard />
    </Stack>
  );
}
