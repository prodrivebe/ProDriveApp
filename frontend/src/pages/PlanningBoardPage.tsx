import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { Link as RouterLink } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { planningService } from "../services/planningService";
import { AssignmentBoard } from "../components/AssignmentBoard";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { useRealtime } from "../hooks/useRealtime";
import type { PlanningOrderCard } from "../types/api";

const COLUMN_ORDER = [
  "unassigned",
  "planned",
  "assigned",
  "loading",
  "in_transit",
  "delivering",
  "completed",
] as const;

const COLUMN_LABELS: Record<(typeof COLUMN_ORDER)[number], string> = {
  unassigned: "Unassigned",
  planned: "Planned",
  assigned: "Assigned",
  loading: "Loading",
  in_transit: "In Transit",
  delivering: "Delivering",
  completed: "Completed",
};

function PlanningCard({ order }: { order: PlanningOrderCard }) {
  return (
    <Card
      variant="outlined"
      draggable
      onDragStart={(event) => event.dataTransfer.setData("orderId", order.id)}
      sx={{ mb: 1, cursor: "grab" }}
    >
      <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
        <Typography
          component={RouterLink}
          to={`/orders/${order.id}`}
          variant="subtitle2"
          sx={{ fontWeight: 700, textDecoration: "none", color: "inherit" }}
        >
          {order.order_number}
        </Typography>
        <Typography variant="caption" display="block">
          {order.vehicle_count} vehicles
        </Typography>
        <Chip size="small" label={order.status.replaceAll("_", " ")} sx={{ mt: 1 }} />
        <Button
          component={RouterLink}
          to={`/planning/loading/${order.id}`}
          size="small"
          sx={{ mt: 1 }}
        >
          Loading board
        </Button>
      </CardContent>
    </Card>
  );
}

export function PlanningBoardPage() {
  const queryClient = useQueryClient();
  useRealtime();
  const [search, setSearch] = useState("");
  const [plannedDate, setPlannedDate] = useState("");
  const [driverId, setDriverId] = useState("");
  const [truckId, setTruckId] = useState("");
  const [trailerId, setTrailerId] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const boardQuery = useQuery({
    queryKey: ["planning", "board", search, plannedDate, driverId, truckId, trailerId],
    queryFn: () =>
      planningService.getBoard({
        search: search || undefined,
        planned_date: plannedDate || undefined,
        driver_id: driverId || undefined,
        truck_id: truckId || undefined,
        trailer_id: trailerId || undefined,
      }),
  });

  const assignMutation = useMutation({
    mutationFn: planningService.assign,
    onSuccess: () => {
      setMessage("Assignment updated.");
      queryClient.invalidateQueries({ queryKey: ["planning"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });

  const board = boardQuery.data;
  const drivers = useMemo(() => board?.drivers ?? [], [board]);
  const trucks = useMemo(() => board?.trucks ?? [], [board]);
  const trailers = useMemo(() => board?.trailers ?? [], [board]);

  const handleDrop = (column: string, orderId: string) => {
    if (column === "assigned" && driverId) {
      assignMutation.mutate({
        order_id: orderId,
        driver_id: driverId,
        truck_id: truckId || undefined,
        trailer_id: trailerId || undefined,
      });
      return;
    }
    if (column === "unassigned") {
      assignMutation.mutate({ order_id: orderId, clear_assignment: true });
    }
  };

  if (boardQuery.isLoading) return <LoadingState label="Loading planning board..." />;
  if (boardQuery.isError) return <ErrorAlert error={boardQuery.error} />;
  if (!board) return null;

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Planning board
      </Typography>
      {message ? <Alert severity="success" onClose={() => setMessage(null)}>{message}</Alert> : null}
      {assignMutation.isError ? <ErrorAlert error={assignMutation.error} /> : null}

      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <TextField label="Search" value={search} onChange={(e) => setSearch(e.target.value)} fullWidth />
            <TextField
              label="Planned date"
              type="date"
              InputLabelProps={{ shrink: true }}
              value={plannedDate}
              onChange={(e) => setPlannedDate(e.target.value)}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Driver</InputLabel>
              <Select label="Driver" value={driverId} onChange={(e) => setDriverId(e.target.value)}>
                <MenuItem value="">Any</MenuItem>
                {drivers.map((driver) => (
                  <MenuItem key={driver.id} value={driver.id}>
                    {driver.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Truck</InputLabel>
              <Select label="Truck" value={truckId} onChange={(e) => setTruckId(e.target.value)}>
                <MenuItem value="">Any</MenuItem>
                {trucks.map((truck) => (
                  <MenuItem key={truck.id} value={truck.id}>
                    {truck.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Trailer</InputLabel>
              <Select label="Trailer" value={trailerId} onChange={(e) => setTrailerId(e.target.value)}>
                <MenuItem value="">Any</MenuItem>
                {trailers.map((trailer) => (
                  <MenuItem key={trailer.id} value={trailer.id}>
                    {trailer.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </CardContent>
      </Card>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 9 }}>
          <Box sx={{ overflowX: "auto", pb: 1 }}>
            <Stack direction="row" spacing={2} sx={{ minWidth: 1200 }}>
              {COLUMN_ORDER.map((column) => (
                <Box
                  key={column}
                  sx={{ minWidth: 220, bgcolor: "action.hover", borderRadius: 2, p: 1.5, minHeight: 360 }}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={(event) => {
                    const orderId = event.dataTransfer.getData("orderId");
                    if (orderId) handleDrop(column, orderId);
                  }}
                >
                  <Typography variant="subtitle1" fontWeight={700}>
                    {COLUMN_LABELS[column]}
                  </Typography>
                  <Chip size="small" label={board.columns[column]?.length ?? 0} sx={{ mb: 1.5 }} />
                  {(board.columns[column] ?? []).map((order) => (
                    <PlanningCard key={order.id} order={order} />
                  ))}
                </Box>
              ))}
            </Stack>
          </Box>
        </Grid>
        <Grid size={{ xs: 12, lg: 3 }}>
          <AssignmentBoard board={board} />
        </Grid>
      </Grid>
    </Stack>
  );
}
