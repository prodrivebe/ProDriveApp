import { Link as RouterLink, useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { driversService } from "../services/driversService";
import { ordersService } from "../services/ordersService";
import { DriverFormDialog } from "../components/DriverFormDialog";
import { formatDriverName } from "../utils/driverDisplay";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { formatDate } from "../utils/format";
import type { DriverUpdatePayload } from "../types/api";

export function DriverDetailPage() {
  const { driverId = "" } = useParams();
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);

  const driverQuery = useQuery({
    queryKey: ["drivers", driverId],
    queryFn: () => driversService.get(driverId),
    enabled: Boolean(driverId),
  });

  const ordersQuery = useQuery({
    queryKey: ["orders", "driver", driverId],
    queryFn: () => ordersService.list({ page: 1, page_size: 50, driver_id: driverId }),
    enabled: Boolean(driverId),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: DriverUpdatePayload) => driversService.update(driverId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drivers", driverId] });
      queryClient.invalidateQueries({ queryKey: ["drivers"] });
      setEditOpen(false);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: () => driversService.update(driverId, { active: false }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drivers", driverId] });
      queryClient.invalidateQueries({ queryKey: ["drivers"] });
    },
  });

  if (driverQuery.isLoading) return <LoadingState />;
  if (driverQuery.isError) return <ErrorAlert error={driverQuery.error} />;

  const driver = driverQuery.data!;
  const activeOrder = ordersQuery.data?.items.find(
    (order) => !["COMPLETED", "CANCELLED"].includes(order.status),
  );

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h4" fontWeight={700}>
          {formatDriverName(driver)}
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setEditOpen(true)}>
            Edit driver
          </Button>
          {driver.active ? (
            <Button
              color="warning"
              variant="outlined"
              onClick={() => deactivateMutation.mutate()}
              disabled={deactivateMutation.isPending}
            >
              Deactivate
            </Button>
          ) : null}
        </Stack>
      </Box>

      <Chip label={driver.active ? "Active" : "Offline"} color={driver.active ? "success" : "default"} />

      {updateMutation.isError ? <ErrorAlert error={updateMutation.error} /> : null}
      {deactivateMutation.isError ? <ErrorAlert error={deactivateMutation.error} /> : null}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Contact
          </Typography>
          <Typography>Phone: {driver.phone ?? "—"}</Typography>
          <Typography>Email: {driver.email ?? "—"}</Typography>
          <Typography>Address: {driver.address ?? "—"}</Typography>
          <Typography>Country: {driver.country ?? "—"}</Typography>
          <Typography>Date of birth: {formatDate(driver.date_of_birth)}</Typography>
          <Typography>Notes: {driver.notes ?? "—"}</Typography>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Documents &amp; expiry
          </Typography>
          <Typography>ID document: {driver.id_document_number ?? "—"}</Typography>
          <Typography>ID expiry: {formatDate(driver.id_expiry)}</Typography>
          <Typography>Driving licence: {driver.driving_license ?? "—"}</Typography>
          <Typography>Driving licence expiry: {formatDate(driver.driving_licence_expiry)}</Typography>
          <Typography>ADR certificate: {driver.adr_certificate ?? "—"}</Typography>
          <Typography>Code 95 expiry: {formatDate(driver.code95_expiry)}</Typography>
          <Typography>Tachograph card: {driver.tachograph_card_number ?? "—"}</Typography>
          <Typography>Tachograph expiry: {formatDate(driver.tachograph_card_expiry)}</Typography>
          <Typography>Visa / residence expiry: {formatDate(driver.visa_residence_expiry)}</Typography>
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

      <DriverFormDialog
        open={editOpen}
        driver={driver}
        onClose={() => setEditOpen(false)}
        onSubmit={(payload) => updateMutation.mutateAsync(payload as DriverUpdatePayload)}
        isSubmitting={updateMutation.isPending}
      />
    </Stack>
  );
}
