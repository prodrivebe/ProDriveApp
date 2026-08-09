import { Link as RouterLink } from "react-router-dom";
import RefreshIcon from "@mui/icons-material/Refresh";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { dashboardService } from "../services/documentsService";
import { notificationsService } from "../services/notificationsService";
import { ordersService } from "../services/ordersService";
import { driversService } from "../services/driversService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { isToday } from "../utils/format";

function StatCard({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
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
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const [orderSearch, setOrderSearch] = useState("");
  const [driverSearch, setDriverSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

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

  const filteredOrders = useMemo(() => {
    if (!dashboardQuery.data) return [];
    let items = dashboardQuery.data.orders.items;
    if (statusFilter !== "ALL") {
      items = items.filter((order) => order.status === statusFilter);
    }
    if (orderSearch.trim()) {
      const q = orderSearch.toLowerCase();
      items = items.filter(
        (order) =>
          order.order_number.toLowerCase().includes(q) ||
          order.notes?.toLowerCase().includes(q),
      );
    }
    return items.slice(0, 8);
  }, [dashboardQuery.data, orderSearch, statusFilter]);

  const filteredDrivers = useMemo(() => {
    if (!dashboardQuery.data) return [];
    let items = dashboardQuery.data.drivers.items;
    if (driverSearch.trim()) {
      const q = driverSearch.toLowerCase();
      items = items.filter((driver) => driver.id.toLowerCase().includes(q) || driver.phone?.includes(q));
    }
    return items.slice(0, 8);
  }, [dashboardQuery.data, driverSearch]);

  if (dashboardQuery.isLoading) return <LoadingState label="Loading operations board..." />;
  if (dashboardQuery.isError) return <ErrorAlert error={dashboardQuery.error} />;

  const { kpi, ordersReport, notifications, orders, drivers } = dashboardQuery.data;
  const byStatus = ordersReport.by_status;

  const waitingAssignment =
    (byStatus.READY ?? 0) + (byStatus.DRAFT ?? 0) + (byStatus.ASSIGNED ?? 0);
  const loadingOrders =
    (byStatus.LOADING ?? 0) + (byStatus.LOADED ?? 0) + (byStatus.ARRIVED_PICKUP ?? 0);
  const inTransit =
    (byStatus.IN_TRANSIT ?? 0) +
    (byStatus.ARRIVED_DELIVERY ?? 0) +
    (byStatus.DELIVERING ?? 0);
  const completedToday = orders.items.filter(
    (order) => order.status === "COMPLETED" && isToday(order.updated_at),
  ).length;
  const delayedOrders = orders.items.filter(
    (order) =>
      !["COMPLETED", "CANCELLED"].includes(order.status) &&
      order.planned_delivery_date &&
      new Date(order.planned_delivery_date) < new Date(),
  ).length;
  const activeDrivers = drivers.items.filter((d) => d.active && orders.items.some((o) => o.assigned_driver_id === d.id));
  const availableDrivers = drivers.items.filter(
    (d) => d.active && !orders.items.some((o) => o.assigned_driver_id === d.id && !["COMPLETED", "CANCELLED"].includes(o.status)),
  );
  const offlineDrivers = drivers.items.filter((d) => !d.active);

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 2, flexWrap: "wrap" }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Operations Board
          </Typography>
          <Typography color="text.secondary">Live transport overview</Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button startIcon={<RefreshIcon />} onClick={() => dashboardQuery.refetch()}>
            Refresh
          </Button>
          <Button component={RouterLink} to="/orders/new" variant="contained">
            Create order
          </Button>
        </Stack>
      </Box>

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        {["ALL", "READY", "IN_TRANSIT", "LOADING", "COMPLETED"].map((status) => (
          <Chip
            key={status}
            label={status.replaceAll("_", " ")}
            color={statusFilter === status ? "primary" : "default"}
            onClick={() => setStatusFilter(status)}
            clickable
          />
        ))}
      </Stack>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Waiting assignment" value={waitingAssignment} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Active orders" value={kpi.active_orders} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Loading" value={loadingOrders} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="In transit" value={inTransit} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Delayed" value={delayedOrders} hint="Past planned delivery" /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Completed today" value={completedToday} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Available drivers" value={availableDrivers.length} /></Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}><StatCard label="Active drivers" value={activeDrivers.length} /></Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Orders
              </Typography>
              <TextField
                size="small"
                fullWidth
                placeholder="Search orders"
                value={orderSearch}
                onChange={(e) => setOrderSearch(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Stack spacing={1}>
                {filteredOrders.map((order) => (
                  <Box key={order.id} sx={{ display: "flex", justifyContent: "space-between", gap: 1 }}>
                    <Button component={RouterLink} to={`/orders/${order.id}`} size="small">
                      {order.order_number}
                    </Button>
                    <Chip size="small" label={order.status.replaceAll("_", " ")} />
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Drivers
              </Typography>
              <TextField
                size="small"
                fullWidth
                placeholder="Search drivers"
                value={driverSearch}
                onChange={(e) => setDriverSearch(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Stack spacing={1}>
                {filteredDrivers.map((driver) => (
                  <Box key={driver.id} sx={{ display: "flex", justifyContent: "space-between" }}>
                    <Button component={RouterLink} to={`/drivers/${driver.id}`} size="small">
                      {driver.phone ?? driver.id.slice(0, 8)}
                    </Button>
                    <Chip size="small" label={driver.active ? "Active" : "Offline"} color={driver.active ? "success" : "default"} />
                  </Box>
                ))}
              </Stack>
              <Alert severity="info" sx={{ mt: 2 }}>
                Offline drivers: {offlineDrivers.length}
              </Alert>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent notifications
              </Typography>
              {notifications.length === 0 ? (
                <Typography color="text.secondary">No unread notifications.</Typography>
              ) : (
                notifications.slice(0, 5).map((item) => (
                  <Box key={item.id} sx={{ mb: 1.5 }}>
                    <Typography fontWeight={600}>{item.title}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {item.message}
                    </Typography>
                  </Box>
                ))
              )}
              <Button component={RouterLink} to="/notifications" size="small">
                View all
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}
