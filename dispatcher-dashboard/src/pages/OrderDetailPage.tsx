import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import {
  apiGet,
  apiGetPaginated,
  apiPost,
  fetchOrderDocuments,
  type OrderDocument,
} from "../api/client";
import { ErrorAlert, StatusChip } from "../components/StatusChip";
import type {
  DriverOption,
  FleetOption,
  OrderDetail,
  SuggestDriverResponse,
  TimelineEntry,
} from "../types/domain";

export function OrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [documents, setDocuments] = useState<OrderDocument[]>([]);
  const [drivers, setDrivers] = useState<DriverOption[]>([]);
  const [trucks, setTrucks] = useState<FleetOption[]>([]);
  const [trailers, setTrailers] = useState<FleetOption[]>([]);
  const [selectedDriverId, setSelectedDriverId] = useState("");
  const [selectedTruckId, setSelectedTruckId] = useState("");
  const [selectedTrailerId, setSelectedTrailerId] = useState("");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadOrder = useCallback(async () => {
    if (!orderId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [orderData, timelineData, documentData, driverData, truckData, trailerData, suggestion] =
        await Promise.all([
          apiGet<OrderDetail>(`/orders/${orderId}`),
          apiGet<TimelineEntry[]>(`/orders/${orderId}/timeline`),
          fetchOrderDocuments(orderId),
          apiGetPaginated<DriverOption>("/drivers?page=1&page_size=100&active=true"),
          apiGetPaginated<FleetOption>("/trucks?page=1&page_size=100&active=true"),
          apiGetPaginated<FleetOption>("/trailers?page=1&page_size=100&active=true"),
          apiPost<SuggestDriverResponse>("/ai/suggest-driver", { order_id: orderId }).catch(
            () => ({ recommended: null }),
          ),
        ]);

      setOrder(orderData);
      setTimeline(timelineData);
      setDocuments(documentData);
      setDrivers(driverData.items);
      setTrucks(truckData.items);
      setTrailers(trailerData.items);
      setSelectedDriverId(
        orderData.assigned_driver_id ?? suggestion.recommended?.driver_id ?? "",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load order.");
      setOrder(null);
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    void loadOrder();
  }, [loadOrder]);

  const pickupCities = useMemo(
    () =>
      order?.stops
        .filter((stop) => stop.stop_type === "PICKUP")
        .map((stop) => stop.city)
        .filter(Boolean)
        .join(", ") ?? "",
    [order],
  );

  const deliveryCities = useMemo(
    () =>
      order?.stops
        .filter((stop) => stop.stop_type === "DELIVERY")
        .map((stop) => stop.city)
        .filter(Boolean)
        .join(", ") ?? "",
    [order],
  );

  const cmrDocuments = useMemo(
    () =>
      documents
        .filter((document) => document.document_type === "CMR" && (document.version ?? 2) >= 2)
        .sort((left, right) => (right.version ?? 0) - (left.version ?? 0)),
    [documents],
  );

  const assignDriver = async () => {
    if (!orderId || !selectedDriverId) {
      return;
    }
    try {
      await apiPost(`/orders/${orderId}/assign-driver`, {
        driver_id: selectedDriverId,
        truck_id: selectedTruckId || null,
        trailer_id: selectedTrailerId || null,
      });
      setSuccessMessage("Driver assigned successfully.");
      await loadOrder();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assignment failed.");
    }
  };

  if (error) {
    return <ErrorAlert message={error} />;
  }

  if (loading || !order) {
    return <Typography>Loading order...</Typography>;
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4">{order.order_number}</Typography>
        <StatusChip status={order.status} />
      </Box>

      {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Route
          </Typography>
          <Typography>Pickup: {pickupCities || "—"}</Typography>
          <Typography>Delivery: {deliveryCities || "—"}</Typography>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Assignment
          </Typography>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel id="driver-label">Driver</InputLabel>
              <Select
                labelId="driver-label"
                label="Driver"
                value={selectedDriverId}
                onChange={(event) => setSelectedDriverId(event.target.value)}
              >
                {drivers.map((driver) => (
                  <MenuItem key={driver.id} value={driver.id}>
                    {driver.user?.first_name} {driver.user?.last_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel id="truck-label">Truck</InputLabel>
              <Select
                labelId="truck-label"
                label="Truck"
                value={selectedTruckId}
                onChange={(event) => setSelectedTruckId(event.target.value)}
              >
                <MenuItem value="">None</MenuItem>
                {trucks.map((truck) => (
                  <MenuItem key={truck.id} value={truck.id}>
                    {truck.registration_number ?? truck.id}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel id="trailer-label">Trailer</InputLabel>
              <Select
                labelId="trailer-label"
                label="Trailer"
                value={selectedTrailerId}
                onChange={(event) => setSelectedTrailerId(event.target.value)}
              >
                <MenuItem value="">None</MenuItem>
                {trailers.map((trailer) => (
                  <MenuItem key={trailer.id} value={trailer.id}>
                    {trailer.registration_number ?? trailer.id}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
          <Box sx={{ mt: 2 }}>
            <Button variant="contained" onClick={() => void assignDriver()} disabled={!selectedDriverId}>
              Assign driver
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Vehicles ({order.vehicles.length})
          </Typography>
          {order.vehicles.map((vehicle) => (
            <Typography key={vehicle.id}>
              {vehicle.make} {vehicle.model} · {vehicle.vin ?? "VIN pending"}
            </Typography>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            CMR documents
          </Typography>
          {cmrDocuments.length === 0 ? (
            <Typography color="text.secondary">No CMR generated yet.</Typography>
          ) : (
            cmrDocuments.map((document) => (
              <Typography key={document.id}>{document.file_path}</Typography>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Timeline
          </Typography>
          {timeline.map((entry) => (
            <Typography key={entry.id}>
              {new Date(entry.created_at).toLocaleString()} · {entry.message}
            </Typography>
          ))}
        </CardContent>
      </Card>
    </Stack>
  );
}
