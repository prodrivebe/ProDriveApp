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
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  Typography,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { ordersService } from "../services/ordersService";
import { driversService } from "../services/driversService";
import { fleetService } from "../services/fleetService";
import { customersService } from "../services/customersService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { PhotoGallery } from "../components/PhotoGallery";
import { StatusChip } from "../components/StatusChip";
import { TimelineViewer } from "../components/TimelineViewer";
import { AiDriverPanel } from "../components/AiDriverPanel";
import { formatDate, formatDateTime, formatStopCities } from "../utils/format";
import { resolveUploadUrl } from "../app/config";
import type { VehiclePhoto } from "../types/api";
import { useRealtime } from "../hooks/useRealtime";

const TABS = ["Overview", "Vehicles", "Timeline", "Photos", "Documents", "Damage"] as const;

export function OrderDetailPage() {
  const { orderId = "" } = useParams();
  const { subscribeOrder } = useRealtime();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState(0);
  const [driverId, setDriverId] = useState("");
  const [truckId, setTruckId] = useState("");
  const [trailerId, setTrailerId] = useState("");
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (orderId) {
      subscribeOrder(orderId);
    }
  }, [orderId, subscribeOrder]);

  const orderQuery = useQuery({
    queryKey: ["orders", orderId],
    queryFn: () => ordersService.get(orderId),
    enabled: Boolean(orderId),
  });

  const timelineQuery = useQuery({
    queryKey: ["orders", orderId, "timeline"],
    queryFn: () => ordersService.timeline(orderId),
    enabled: Boolean(orderId),
  });

  const checklistQuery = useQuery({
    queryKey: ["orders", orderId, "checklist"],
    queryFn: () => ordersService.checklist(orderId),
    enabled: Boolean(orderId),
  });

  const documentsQuery = useQuery({
    queryKey: ["orders", orderId, "documents"],
    queryFn: () => ordersService.listDocuments(orderId),
    enabled: Boolean(orderId),
  });

  const driversQuery = useQuery({
    queryKey: ["drivers"],
    queryFn: () => driversService.list({ page: 1, page_size: 100, active: true }),
  });
  const trucksQuery = useQuery({
    queryKey: ["trucks"],
    queryFn: () => fleetService.listTrucks({ page: 1, page_size: 100, active: true }),
  });
  const trailersQuery = useQuery({
    queryKey: ["trailers"],
    queryFn: () => fleetService.listTrailers({ page: 1, page_size: 100, active: true }),
  });
  const customerQuery = useQuery({
    queryKey: ["customers", orderQuery.data?.customer_id],
    queryFn: () => customersService.get(orderQuery.data!.customer_id),
    enabled: Boolean(orderQuery.data?.customer_id),
  });

  const photoQueries = useQueries({
    queries: (orderQuery.data?.vehicles ?? []).map((vehicle) => ({
      queryKey: ["orders", orderId, "photos", vehicle.id],
      queryFn: () => ordersService.listVehiclePhotos(orderId, vehicle.id),
      enabled: Boolean(orderId),
    })),
  });

  const damageQueries = useQueries({
    queries: (orderQuery.data?.vehicles ?? []).map((vehicle) => ({
      queryKey: ["orders", orderId, "damage", vehicle.id],
      queryFn: () => ordersService.listVehicleDamage(orderId, vehicle.id),
      enabled: Boolean(orderId),
    })),
  });

  const assignMutation = useMutation({
    mutationFn: () =>
      ordersService.assignDriver(orderId, {
        driver_id: driverId,
        truck_id: truckId || null,
        trailer_id: trailerId || null,
      }),
    onSuccess: () => {
      setSuccess("Driver assigned successfully.");
      queryClient.invalidateQueries({ queryKey: ["orders", orderId] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => ordersService.uploadDocument(orderId, file, "CMR"),
    onSuccess: () => {
      setSuccess("Document uploaded.");
      queryClient.invalidateQueries({ queryKey: ["orders", orderId, "documents"] });
    },
  });

  if (orderQuery.isLoading) return <LoadingState label="Loading order..." />;
  if (orderQuery.isError) return <ErrorAlert error={orderQuery.error} />;
  const order = orderQuery.data!;

  const allPhotos: VehiclePhoto[] = photoQueries.flatMap((q) => q.data ?? []);
  const allDamage = damageQueries.flatMap((q) => q.data ?? []);

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" fontWeight={700}>
          {order.order_number}
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
          <StatusChip status={order.status} />
          <Typography color="text.secondary">
            Customer: {customerQuery.data?.company_name ?? "—"}
          </Typography>
        </Stack>
      </Box>

      {success ? <Alert severity="success" onClose={() => setSuccess(null)}>{success}</Alert> : null}

      <Tabs value={tab} onChange={(_, value) => setTab(value)} variant="scrollable">
        {TABS.map((label) => (
          <Tab key={label} label={label} />
        ))}
      </Tabs>

      {tab === 0 ? (
        <Stack spacing={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Order summary
              </Typography>
              <Typography>Pickup: {formatStopCities(order.stops, "PICKUP")}</Typography>
              <Typography>Delivery: {formatStopCities(order.stops, "DELIVERY")}</Typography>
              <Typography>Planned pickup: {formatDate(order.planned_pickup_date)}</Typography>
              <Typography>Planned delivery: {formatDate(order.planned_delivery_date)}</Typography>
              <Typography>Vehicles: {order.vehicles.length}</Typography>
              <Typography>Notes: {order.notes || "—"}</Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Assign driver
              </Typography>
              <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                <FormControl fullWidth>
                  <InputLabel>Driver</InputLabel>
                  <Select
                    label="Driver"
                    value={driverId || order.assigned_driver_id || ""}
                    onChange={(e) => setDriverId(e.target.value)}
                  >
                    {driversQuery.data?.items.map((driver) => (
                      <MenuItem key={driver.id} value={driver.id}>
                        {driver.phone ?? driver.id.slice(0, 8)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl fullWidth>
                  <InputLabel>Truck</InputLabel>
                  <Select label="Truck" value={truckId} onChange={(e) => setTruckId(e.target.value)}>
                    <MenuItem value="">None</MenuItem>
                    {trucksQuery.data?.items.map((truck) => (
                      <MenuItem key={truck.id} value={truck.id}>
                        {truck.registration_number}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl fullWidth>
                  <InputLabel>Trailer</InputLabel>
                  <Select label="Trailer" value={trailerId} onChange={(e) => setTrailerId(e.target.value)}>
                    <MenuItem value="">None</MenuItem>
                    {trailersQuery.data?.items.map((trailer) => (
                      <MenuItem key={trailer.id} value={trailer.id}>
                        {trailer.registration_number}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button
                  variant="contained"
                  onClick={() => assignMutation.mutate()}
                  disabled={!driverId && !order.assigned_driver_id}
                >
                  Assign
                </Button>
              </Stack>
            </CardContent>
          </Card>

          <AiDriverPanel orderId={orderId} onSelectDriver={setDriverId} />

          {checklistQuery.data ? (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Completion checklist
                </Typography>
                <Typography gutterBottom>
                  {checklistQuery.data.completion_percentage}% complete
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={checklistQuery.data.completion_percentage}
                  sx={{ mb: 2 }}
                />
                <Typography>
                  Can complete: {checklistQuery.data.can_complete ? "Yes" : "No"}
                </Typography>
                {checklistQuery.data.missing_items.length ? (
                  <Typography color="text.secondary">
                    Missing: {checklistQuery.data.missing_items.join(", ")}
                  </Typography>
                ) : null}
              </CardContent>
            </Card>
          ) : null}
        </Stack>
      ) : null}

      {tab === 1 ? (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Make</TableCell>
              <TableCell>Model</TableCell>
              <TableCell>VIN</TableCell>
              <TableCell>Verified VIN</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {order.vehicles.map((vehicle) => (
              <TableRow key={vehicle.id}>
                <TableCell>{vehicle.make ?? "—"}</TableCell>
                <TableCell>{vehicle.model ?? "—"}</TableCell>
                <TableCell>{vehicle.vin ?? "—"}</TableCell>
                <TableCell>{vehicle.verified_vin ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}

      {tab === 2 ? (
        timelineQuery.isLoading ? (
          <LoadingState />
        ) : (
          <TimelineViewer entries={timelineQuery.data ?? []} />
        )
      ) : null}

      {tab === 3 ? (
        allPhotos.length ? (
          <PhotoGallery photos={allPhotos} />
        ) : (
          <Typography color="text.secondary">No photos uploaded yet.</Typography>
        )
      ) : null}

      {tab === 4 ? (
        <Stack spacing={2}>
          <Button
            component="label"
            variant="outlined"
            startIcon={<UploadFileIcon />}
            disabled={uploadMutation.isPending}
          >
            Upload CMR
            <input
              hidden
              type="file"
              accept="image/*,application/pdf"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) uploadMutation.mutate(file);
              }}
            />
          </Button>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>File</TableCell>
                <TableCell>Version</TableCell>
                <TableCell>Uploaded</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {(documentsQuery.data ?? []).map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.document_type}</TableCell>
                  <TableCell>{doc.file_name}</TableCell>
                  <TableCell>v{doc.version}</TableCell>
                  <TableCell>{formatDateTime(doc.uploaded_at)}</TableCell>
                  <TableCell>
                    <Button href={resolveUploadUrl(doc.file_path)} target="_blank" size="small">
                      Preview
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Stack>
      ) : null}

      {tab === 5 ? (
        allDamage.length ? (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Location</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Reported</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {allDamage.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.damage_type}</TableCell>
                  <TableCell>{item.severity}</TableCell>
                  <TableCell>{item.location ?? "—"}</TableCell>
                  <TableCell>{item.description ?? "—"}</TableCell>
                  <TableCell>{formatDateTime(item.reported_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Typography color="text.secondary">No damage reports.</Typography>
        )
      ) : null}
    </Stack>
  );
}
