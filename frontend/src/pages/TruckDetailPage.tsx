import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { fleetService } from "../services/fleetService";
import { TruckFormDialog } from "../components/TruckFormDialog";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { formatDate } from "../utils/format";
import type {
  TruckInspectionCreatePayload,
  TruckMaintenanceCreatePayload,
  TruckTireCreatePayload,
  TruckUpdatePayload,
} from "../types/api";

export function TruckDetailPage() {
  const { truckId = "" } = useParams();
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);

  const [maintenanceForm, setMaintenanceForm] = useState<TruckMaintenanceCreatePayload>({
    maintenance_date: "",
    maintenance_type: "",
    mileage: null,
    notes: "",
  });
  const [inspectionForm, setInspectionForm] = useState<TruckInspectionCreatePayload>({
    inspection_date: "",
    inspection_type: "",
    mileage: null,
    notes: "",
  });
  const [tireForm, setTireForm] = useState<TruckTireCreatePayload>({
    tire_date: "",
    tire_type: "",
    mileage: null,
    notes: "",
  });

  const truckQuery = useQuery({
    queryKey: ["trucks", truckId],
    queryFn: () => fleetService.getTruck(truckId),
    enabled: Boolean(truckId),
  });

  const maintenanceQuery = useQuery({
    queryKey: ["trucks", truckId, "maintenance"],
    queryFn: () => fleetService.listMaintenanceRecords(truckId),
    enabled: Boolean(truckId),
  });

  const inspectionQuery = useQuery({
    queryKey: ["trucks", truckId, "inspections"],
    queryFn: () => fleetService.listInspectionRecords(truckId),
    enabled: Boolean(truckId),
  });

  const tireQuery = useQuery({
    queryKey: ["trucks", truckId, "tires"],
    queryFn: () => fleetService.listTireRecords(truckId),
    enabled: Boolean(truckId),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: TruckUpdatePayload) => fleetService.updateTruck(truckId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trucks", truckId] });
      queryClient.invalidateQueries({ queryKey: ["trucks"] });
      setEditOpen(false);
    },
  });

  const maintenanceMutation = useMutation({
    mutationFn: (payload: TruckMaintenanceCreatePayload) =>
      fleetService.createMaintenanceRecord(truckId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trucks", truckId, "maintenance"] });
      setMaintenanceForm({ maintenance_date: "", maintenance_type: "", mileage: null, notes: "" });
    },
  });

  const inspectionMutation = useMutation({
    mutationFn: (payload: TruckInspectionCreatePayload) =>
      fleetService.createInspectionRecord(truckId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trucks", truckId, "inspections"] });
      setInspectionForm({ inspection_date: "", inspection_type: "", mileage: null, notes: "" });
    },
  });

  const tireMutation = useMutation({
    mutationFn: (payload: TruckTireCreatePayload) => fleetService.createTireRecord(truckId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trucks", truckId, "tires"] });
      setTireForm({ tire_date: "", tire_type: "", mileage: null, notes: "" });
    },
  });

  if (truckQuery.isLoading) return <LoadingState />;
  if (truckQuery.isError) return <ErrorAlert error={truckQuery.error} />;

  const truck = truckQuery.data!;

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h4" fontWeight={700}>
          {truck.registration_number}
        </Typography>
        <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setEditOpen(true)}>
          Edit truck
        </Button>
      </Box>

      {updateMutation.isError ? <ErrorAlert error={updateMutation.error} /> : null}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Truck profile
          </Typography>
          <Typography>Brand / model: {[truck.brand, truck.model].filter(Boolean).join(" ") || "—"}</Typography>
          <Typography>VIN: {truck.vin ?? "—"}</Typography>
          <Typography>Capacity: {truck.capacity ?? "—"}</Typography>
          <Typography>
            Current mileage: {truck.current_mileage != null ? `${truck.current_mileage} km` : "—"}
          </Typography>
          <Typography>Status: {truck.active ? "Active" : "Inactive"}</Typography>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Maintenance
          </Typography>
          {maintenanceQuery.isError ? <ErrorAlert error={maintenanceQuery.error} /> : null}
          {maintenanceMutation.isError ? <ErrorAlert error={maintenanceMutation.error} /> : null}
          <Table size="small" sx={{ mb: 2 }}>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Mileage</TableCell>
                <TableCell>Notes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(maintenanceQuery.data ?? []).map((record) => (
                <TableRow key={record.id}>
                  <TableCell>{formatDate(record.maintenance_date)}</TableCell>
                  <TableCell>{record.maintenance_type}</TableCell>
                  <TableCell>{record.mileage ?? "—"}</TableCell>
                  <TableCell>{record.notes ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
            <TextField
              label="Date"
              type="date"
              InputLabelProps={{ shrink: true }}
              value={maintenanceForm.maintenance_date}
              onChange={(e) => setMaintenanceForm({ ...maintenanceForm, maintenance_date: e.target.value })}
            />
            <TextField
              label="Type"
              value={maintenanceForm.maintenance_type}
              onChange={(e) => setMaintenanceForm({ ...maintenanceForm, maintenance_type: e.target.value })}
            />
            <TextField
              label="Mileage"
              type="number"
              value={maintenanceForm.mileage ?? ""}
              onChange={(e) =>
                setMaintenanceForm({
                  ...maintenanceForm,
                  mileage: e.target.value ? Number(e.target.value) : null,
                })
              }
            />
            <Button
              variant="contained"
              onClick={() => maintenanceMutation.mutate(maintenanceForm)}
              disabled={!maintenanceForm.maintenance_date || !maintenanceForm.maintenance_type}
            >
              Add
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Inspections
          </Typography>
          {inspectionQuery.isError ? <ErrorAlert error={inspectionQuery.error} /> : null}
          {inspectionMutation.isError ? <ErrorAlert error={inspectionMutation.error} /> : null}
          <Table size="small" sx={{ mb: 2 }}>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Mileage</TableCell>
                <TableCell>Notes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(inspectionQuery.data ?? []).map((record) => (
                <TableRow key={record.id}>
                  <TableCell>{formatDate(record.inspection_date)}</TableCell>
                  <TableCell>{record.inspection_type}</TableCell>
                  <TableCell>{record.mileage ?? "—"}</TableCell>
                  <TableCell>{record.notes ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
            <TextField
              label="Date"
              type="date"
              InputLabelProps={{ shrink: true }}
              value={inspectionForm.inspection_date}
              onChange={(e) => setInspectionForm({ ...inspectionForm, inspection_date: e.target.value })}
            />
            <TextField
              label="Type"
              value={inspectionForm.inspection_type}
              onChange={(e) => setInspectionForm({ ...inspectionForm, inspection_type: e.target.value })}
            />
            <TextField
              label="Mileage"
              type="number"
              value={inspectionForm.mileage ?? ""}
              onChange={(e) =>
                setInspectionForm({
                  ...inspectionForm,
                  mileage: e.target.value ? Number(e.target.value) : null,
                })
              }
            />
            <Button
              variant="contained"
              onClick={() => inspectionMutation.mutate(inspectionForm)}
              disabled={!inspectionForm.inspection_date || !inspectionForm.inspection_type}
            >
              Add
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Tires
          </Typography>
          {tireQuery.isError ? <ErrorAlert error={tireQuery.error} /> : null}
          {tireMutation.isError ? <ErrorAlert error={tireMutation.error} /> : null}
          <Table size="small" sx={{ mb: 2 }}>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Mileage</TableCell>
                <TableCell>Notes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(tireQuery.data ?? []).map((record) => (
                <TableRow key={record.id}>
                  <TableCell>{formatDate(record.tire_date)}</TableCell>
                  <TableCell>{record.tire_type}</TableCell>
                  <TableCell>{record.mileage ?? "—"}</TableCell>
                  <TableCell>{record.notes ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
            <TextField
              label="Date"
              type="date"
              InputLabelProps={{ shrink: true }}
              value={tireForm.tire_date}
              onChange={(e) => setTireForm({ ...tireForm, tire_date: e.target.value })}
            />
            <TextField
              label="Type"
              value={tireForm.tire_type}
              onChange={(e) => setTireForm({ ...tireForm, tire_type: e.target.value })}
            />
            <TextField
              label="Mileage"
              type="number"
              value={tireForm.mileage ?? ""}
              onChange={(e) =>
                setTireForm({
                  ...tireForm,
                  mileage: e.target.value ? Number(e.target.value) : null,
                })
              }
            />
            <Button
              variant="contained"
              onClick={() => tireMutation.mutate(tireForm)}
              disabled={!tireForm.tire_date || !tireForm.tire_type}
            >
              Add
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <TruckFormDialog
        open={editOpen}
        truck={truck}
        onClose={() => setEditOpen(false)}
        onSubmit={(payload) => updateMutation.mutateAsync(payload as TruckUpdatePayload)}
        isSubmitting={updateMutation.isPending}
      />
    </Stack>
  );
}
