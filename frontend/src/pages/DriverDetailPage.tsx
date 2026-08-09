import { Link as RouterLink, useParams } from "react-router-dom";
import { Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { driversService } from "../services/driversService";
import { ordersService } from "../services/ordersService";
import { apiGet } from "../services/apiClient";
import type { UserProfile } from "../types/api";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";

export function DriverDetailPage() {
  const { driverId = "" } = useParams();

  const driverQuery = useQuery({
    queryKey: ["drivers", driverId],
    queryFn: () => driversService.get(driverId),
    enabled: Boolean(driverId),
  });

  const userQuery = useQuery({
    queryKey: ["users", driverQuery.data?.user_id],
    queryFn: () => apiGet<UserProfile>(`/users/${driverQuery.data!.user_id}`),
    enabled: Boolean(driverQuery.data?.user_id),
  });

  const ordersQuery = useQuery({
    queryKey: ["orders", "driver", driverId],
    queryFn: () => ordersService.list({ page: 1, page_size: 50, driver_id: driverId }),
    enabled: Boolean(driverId),
  });

  if (driverQuery.isLoading) return <LoadingState />;
  if (driverQuery.isError) return <ErrorAlert error={driverQuery.error} />;

  const driver = driverQuery.data!;
  const activeOrder = ordersQuery.data?.items.find(
    (order) => !["COMPLETED", "CANCELLED"].includes(order.status),
  );

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        {userQuery.data ? `${userQuery.data.first_name} ${userQuery.data.last_name}` : "Driver"}
      </Typography>
      <Chip label={driver.active ? "Active" : "Offline"} color={driver.active ? "success" : "default"} />

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Contact
          </Typography>
          <Typography>Phone: {driver.phone ?? "—"}</Typography>
          <Typography>Email: {userQuery.data?.email ?? "—"}</Typography>
          <Typography>Notes: {driver.notes ?? "—"}</Typography>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Current assignment
          </Typography>
          {activeOrder ? (
            <RouterLink to={`/orders/${activeOrder.id}`}>{activeOrder.order_number}</RouterLink>
          ) : (
            <Typography color="text.secondary">No active order.</Typography>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Order history
          </Typography>
          {(ordersQuery.data?.items ?? []).map((order) => (
            <Typography key={order.id}>
              <RouterLink to={`/orders/${order.id}`}>{order.order_number}</RouterLink> — {order.status}
            </Typography>
          ))}
        </CardContent>
      </Card>
    </Stack>
  );
}
