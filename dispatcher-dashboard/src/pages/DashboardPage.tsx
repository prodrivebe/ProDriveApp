import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { apiGet } from "../services/apiClient";
import type { KpiDashboard, Notification, OrdersReport } from "../types/api";

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <Card>
      <CardContent>
        <Typography color="text.secondary" variant="body2">
          {label}
        </Typography>
        <Typography variant="h4" fontWeight={700}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const [kpi, setKpi] = useState<KpiDashboard | null>(null);
  const [ordersReport, setOrdersReport] = useState<OrdersReport | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [kpiData, ordersData, notificationData] = await Promise.all([
          apiGet<KpiDashboard>("/reports/kpi"),
          apiGet<OrdersReport>("/reports/orders"),
          apiGet<Notification[]>("/notifications?unread_only=true"),
        ]);
        setKpi(kpiData);
        setOrdersReport(ordersData);
        setNotifications(notificationData.slice(0, 5));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard.");
      }
    };
    void load();
  }, []);

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!kpi || !ordersReport) {
    return <Typography>Loading dashboard...</Typography>;
  }

  const waitingAssignment =
    (ordersReport.by_status.ASSIGNED ?? 0) +
    (ordersReport.by_status.READY ?? 0) +
    (ordersReport.by_status.DRAFT ?? 0);

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Operations Board
          </Typography>
          <Typography color="text.secondary">
            Today&apos;s transport overview
          </Typography>
        </Box>
        <Button component={RouterLink} to="/orders/new" variant="contained">
          Create order
        </Button>
      </Box>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard label="Active orders" value={kpi.active_orders} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard label="Completed orders" value={kpi.completed_orders} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard label="Waiting assignment" value={waitingAssignment} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard label="Active drivers" value={kpi.active_drivers} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Fleet snapshot
              </Typography>
              <Typography>Drivers: {kpi.fleet.drivers.active}/{kpi.fleet.drivers.total} active</Typography>
              <Typography>Trucks: {kpi.fleet.trucks.active}/{kpi.fleet.trucks.total} active</Typography>
              <Typography>Trailers: {kpi.fleet.trailers.active}/{kpi.fleet.trailers.total} active</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Unread notifications
              </Typography>
              {notifications.length === 0 ? (
                <Typography color="text.secondary">No unread alerts.</Typography>
              ) : (
                notifications.map((item) => (
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
