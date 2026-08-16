import {
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { apiGet } from "../api/client";
import { ErrorAlert } from "../components/StatusChip";

interface KpiDashboard {
  active_orders: number;
  completed_orders: number;
  active_drivers: number;
  fleet: {
    drivers: { total: number; active: number };
    trucks: { total: number; active: number };
    trailers: { total: number; active: number };
  };
}

interface OrdersReport {
  by_status: Record<string, number>;
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent>
        <Typography color="text.secondary" variant="body2">
          {label}
        </Typography>
        <Typography variant="h5">{value}</Typography>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const [kpi, setKpi] = useState<KpiDashboard | null>(null);
  const [ordersReport, setOrdersReport] = useState<OrdersReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [kpiData, ordersData] = await Promise.all([
          apiGet<KpiDashboard>("/reports/kpi"),
          apiGet<OrdersReport>("/reports/orders"),
        ]);
        setKpi(kpiData);
        setOrdersReport(ordersData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard.");
      }
    })();
  }, []);

  if (error) {
    return <ErrorAlert message={error} />;
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
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Box>
          <Typography variant="h4">Operations Board</Typography>
          <Typography color="text.secondary">Today&apos;s transport overview</Typography>
        </Box>
        <Button component={RouterLink} to="/orders/new" variant="contained">
          Create order
        </Button>
      </Stack>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard label="Active orders" value={kpi.active_orders} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard label="Completed orders" value={kpi.completed_orders} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard label="Waiting assignment" value={waitingAssignment} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard label="Active drivers" value={kpi.active_drivers} />
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Fleet snapshot
          </Typography>
          <Typography>
            Drivers: {kpi.fleet.drivers.active}/{kpi.fleet.drivers.total} active
          </Typography>
          <Typography>
            Trucks: {kpi.fleet.trucks.active}/{kpi.fleet.trucks.total} active
          </Typography>
          <Typography>
            Trailers: {kpi.fleet.trailers.active}/{kpi.fleet.trailers.total} active
          </Typography>
        </CardContent>
      </Card>
    </Stack>
  );
}

export function PlaceholderPage({ title }: { title: string }) {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">{title}</Typography>
      <Typography color="text.secondary">Module available in this build shell.</Typography>
    </Stack>
  );
}
