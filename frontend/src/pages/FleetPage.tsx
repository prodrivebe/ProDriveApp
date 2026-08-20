import { Link as RouterLink } from "react-router-dom";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
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
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { fleetService } from "../services/fleetService";
import { TruckFormDialog } from "../components/TruckFormDialog";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import type { Truck, TruckCreatePayload, TruckUpdatePayload } from "../types/api";

export function FleetPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTruck, setEditingTruck] = useState<Truck | null>(null);

  const overviewQuery = useQuery({
    queryKey: ["fleet", "overview"],
    queryFn: fleetService.overview,
  });
  const trucksQuery = useQuery({
    queryKey: ["trucks"],
    queryFn: () => fleetService.listTrucks({ page: 1, page_size: 100 }),
  });
  const trailersQuery = useQuery({
    queryKey: ["trailers"],
    queryFn: () => fleetService.listTrailers({ page: 1, page_size: 100 }),
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: TruckCreatePayload | TruckUpdatePayload) => {
      if (editingTruck) {
        return fleetService.updateTruck(editingTruck.id, payload as TruckUpdatePayload);
      }
      return fleetService.createTruck(payload as TruckCreatePayload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trucks"] });
      queryClient.invalidateQueries({ queryKey: ["fleet", "overview"] });
      setDialogOpen(false);
      setEditingTruck(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (truckId: string) => fleetService.deleteTruck(truckId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trucks"] });
      queryClient.invalidateQueries({ queryKey: ["fleet", "overview"] });
    },
  });

  if (overviewQuery.isLoading) return <LoadingState label="Loading fleet..." />;
  if (overviewQuery.isError) return <ErrorAlert error={overviewQuery.error} />;

  const overview = overviewQuery.data;

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h4" fontWeight={700}>
          Fleet
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingTruck(null);
            setDialogOpen(true);
          }}
        >
          Add truck
        </Button>
      </Box>

      {saveMutation.isError ? <ErrorAlert error={saveMutation.error} /> : null}
      {deleteMutation.isError ? <ErrorAlert error={deleteMutation.error} /> : null}

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Trucks</Typography>
              <Typography variant="h4">
                {overview.trucks.active}/{overview.trucks.total}
              </Typography>
              <Typography color="text.secondary">Active trucks</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Trailers</Typography>
              <Typography variant="h4">
                {overview.trailers.active}/{overview.trailers.total}
              </Typography>
              <Typography color="text.secondary">Active trailers</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Drivers</Typography>
              <Typography variant="h4">
                {overview.drivers.active}/{overview.drivers.total}
              </Typography>
              <Typography color="text.secondary">Active drivers</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="h6" gutterBottom>
            Trucks
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Registration</TableCell>
                <TableCell>Brand / Model</TableCell>
                <TableCell>Mileage</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(trucksQuery.data?.items ?? []).map((truck) => (
                <TableRow key={truck.id} hover>
                  <TableCell>
                    <RouterLink to={`/fleet/trucks/${truck.id}`}>{truck.registration_number}</RouterLink>
                  </TableCell>
                  <TableCell>{[truck.brand, truck.model].filter(Boolean).join(" ") || "—"}</TableCell>
                  <TableCell>{truck.current_mileage != null ? `${truck.current_mileage} km` : "—"}</TableCell>
                  <TableCell>{truck.active ? "Active" : "Inactive"}</TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      startIcon={<EditIcon />}
                      onClick={() => {
                        setEditingTruck(truck);
                        setDialogOpen(true);
                      }}
                    >
                      Edit
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      onClick={() => {
                        if (window.confirm(`Delete truck ${truck.registration_number}?`)) {
                          deleteMutation.mutate(truck.id);
                        }
                      }}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="h6" gutterBottom>
            Trailers
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Registration</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(trailersQuery.data?.items ?? []).map((trailer) => (
                <TableRow key={trailer.id}>
                  <TableCell>{trailer.registration_number}</TableCell>
                  <TableCell>{trailer.trailer_type ?? "—"}</TableCell>
                  <TableCell>{trailer.active ? "Active" : "Inactive"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Grid>
      </Grid>

      <TruckFormDialog
        open={dialogOpen}
        truck={editingTruck}
        onClose={() => {
          setDialogOpen(false);
          setEditingTruck(null);
        }}
        onSubmit={(payload) => saveMutation.mutateAsync(payload)}
        isSubmitting={saveMutation.isPending}
      />
    </Stack>
  );
}
