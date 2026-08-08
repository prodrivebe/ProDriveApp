import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { StatusChip } from "../components/StatusChip";
import { apiGet, apiGetList, apiPost } from "../services/apiClient";
import type {
  Driver,
  DriverSuggestion,
  OrderDetail,
  OrderTimelineEntry,
  Trailer,
  Truck,
} from "../types/api";

export function OrderDetailPage() {
  const { orderId } = useParams();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [timeline, setTimeline] = useState<OrderTimelineEntry[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [trailers, setTrailers] = useState<Trailer[]>([]);
  const [selectedDriver, setSelectedDriver] = useState("");
  const [selectedTruck, setSelectedTruck] = useState("");
  const [selectedTrailer, setSelectedTrailer] = useState("");
  const [suggestion, setSuggestion] = useState<DriverSuggestion | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!orderId) return;
    try {
      const [orderData, timelineData, driversResult, trucksResult, trailersResult, aiData] =
        await Promise.all([
          apiGet<OrderDetail>(`/orders/${orderId}`),
          apiGet<OrderTimelineEntry[]>(`/orders/${orderId}/timeline`),
          apiGetList<Driver>("/drivers?page=1&page_size=100&active=true"),
          apiGetList<Truck>("/trucks?page=1&page_size=100&active=true"),
          apiGetList<Trailer>("/trailers?page=1&page_size=100&active=true"),
          apiPost<{ recommended: DriverSuggestion | null }>("/ai/suggest-driver", {
            order_id: orderId,
          }).catch(() => ({ recommended: null })),
        ]);
      setOrder(orderData);
      setTimeline(timelineData);
      setDrivers(driversResult.items);
      setTrucks(trucksResult.items);
      setTrailers(trailersResult.items);
      setSuggestion(aiData.recommended);
      setSelectedDriver(orderData.assigned_driver_id ?? aiData.recommended?.driver_id ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load order.");
    }
  };

  useEffect(() => {
    void load();
  }, [orderId]);

  const assignDriver = async () => {
    if (!orderId || !selectedDriver) return;
    try {
      await apiPost(`/orders/${orderId}/assign-driver`, {
        driver_id: selectedDriver,
        truck_id: selectedTruck || null,
        trailer_id: selectedTrailer || null,
      });
      setMessage("Driver assigned successfully.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assignment failed.");
    }
  };

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!order) {
    return <Typography>Loading order...</Typography>;
  }

  const pickupCities = order.stops
    .filter((stop) => stop.stop_type === "PICKUP")
    .map((stop) => stop.city)
    .filter(Boolean)
    .join(", ");

  const deliveryCities = order.stops
    .filter((stop) => stop.stop_type === "DELIVERY")
    .map((stop) => stop.city)
    .filter(Boolean)
    .join(", ");

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" fontWeight={700}>
          {order.order_number}
        </Typography>
        <StatusChip status={order.status} />
      </Box>

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Order summary
          </Typography>
          <Typography>Pickup: {pickupCities || "—"}</Typography>
          <Typography>Delivery: {deliveryCities || "—"}</Typography>
          <Typography>Vehicles: {order.vehicles.length}</Typography>
          <Typography>Notes: {order.notes || "—"}</Typography>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Assign driver
          </Typography>
          {suggestion ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              AI suggests {suggestion.driver_name} — {suggestion.reason}
            </Alert>
          ) : null}
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel>Driver</InputLabel>
              <Select
                value={selectedDriver}
                label="Driver"
                onChange={(e) => setSelectedDriver(e.target.value)}
              >
                {drivers.map((driver) => (
                  <MenuItem key={driver.id} value={driver.id}>
                    {driver.id.slice(0, 8)}...
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Truck</InputLabel>
              <Select
                value={selectedTruck}
                label="Truck"
                onChange={(e) => setSelectedTruck(e.target.value)}
              >
                <MenuItem value="">None</MenuItem>
                {trucks.map((truck) => (
                  <MenuItem key={truck.id} value={truck.id}>
                    {truck.registration_number}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Trailer</InputLabel>
              <Select
                value={selectedTrailer}
                label="Trailer"
                onChange={(e) => setSelectedTrailer(e.target.value)}
              >
                <MenuItem value="">None</MenuItem>
                {trailers.map((trailer) => (
                  <MenuItem key={trailer.id} value={trailer.id}>
                    {trailer.registration_number}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button variant="contained" onClick={assignDriver} sx={{ minWidth: 160 }}>
              Assign
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Vehicles
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Make</TableCell>
                <TableCell>Model</TableCell>
                <TableCell>VIN</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {order.vehicles.map((vehicle) => (
                <TableRow key={vehicle.id}>
                  <TableCell>{vehicle.make ?? "—"}</TableCell>
                  <TableCell>{vehicle.model ?? "—"}</TableCell>
                  <TableCell>{vehicle.vin ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Timeline
          </Typography>
          {timeline.map((entry) => (
            <Box key={entry.id} sx={{ mb: 1.5 }}>
              <Typography fontWeight={600}>{entry.event_type}</Typography>
              <Typography variant="body2">{entry.description}</Typography>
              <Typography variant="caption" color="text.secondary">
                {new Date(entry.created_at).toLocaleString()}
              </Typography>
            </Box>
          ))}
        </CardContent>
      </Card>
    </Stack>
  );
}
