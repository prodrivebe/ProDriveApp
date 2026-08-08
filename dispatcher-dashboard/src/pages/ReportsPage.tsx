import { useEffect, useState } from "react";
import {
  Alert,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { apiGet } from "../services/apiClient";
import type {
  CustomersReport,
  DriversReport,
  FleetReport,
  OrdersReport,
} from "../types/api";

export function ReportsPage() {
  const [orders, setOrders] = useState<OrdersReport | null>(null);
  const [drivers, setDrivers] = useState<DriversReport | null>(null);
  const [customers, setCustomers] = useState<CustomersReport | null>(null);
  const [fleet, setFleet] = useState<FleetReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [ordersData, driversData, customersData, fleetData] = await Promise.all([
          apiGet<OrdersReport>("/reports/orders"),
          apiGet<DriversReport>("/reports/drivers"),
          apiGet<CustomersReport>("/reports/customers"),
          apiGet<FleetReport>("/reports/fleet"),
        ]);
        setOrders(ordersData);
        setDrivers(driversData);
        setCustomers(customersData);
        setFleet(fleetData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load reports.");
      }
    };
    void load();
  }, []);

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Reports
      </Typography>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Orders</Typography>
              <Typography>Total: {orders?.total_orders ?? 0}</Typography>
              <Typography>Active: {orders?.active_orders ?? 0}</Typography>
              <Typography>Completed: {orders?.completed_orders ?? 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Drivers</Typography>
              <Typography>Total: {drivers?.total_drivers ?? 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Customers</Typography>
              <Typography>Total: {customers?.total_customers ?? 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Fleet utilization</Typography>
              <Typography>Assigned drivers: {fleet?.assigned_drivers ?? 0}</Typography>
              <Typography>Assigned trucks: {fleet?.assigned_trucks ?? 0}</Typography>
              <Typography>Assigned trailers: {fleet?.assigned_trailers ?? 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}
