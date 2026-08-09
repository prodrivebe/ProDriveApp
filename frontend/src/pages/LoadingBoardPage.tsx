import { useEffect, useMemo, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";
import {
  Alert,
  Button,
  Stack,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ordersService } from "../services/ordersService";
import { fleetService } from "../services/fleetService";
import { planningService } from "../services/planningService";
import { TrailerVisualization } from "../components/TrailerVisualization";
import { OptimizationPanel } from "../components/OptimizationPanel";
import { ValidationPanel } from "../components/ValidationPanel";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { useRealtime } from "../hooks/useRealtime";
import type { LoadingPositionDraft, OptimizationResponse, ValidationResponse } from "../types/api";

export function LoadingBoardPage() {
  const { orderId = "" } = useParams();
  const queryClient = useQueryClient();
  useRealtime();
  const [positions, setPositions] = useState<LoadingPositionDraft[]>([]);
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const orderQuery = useQuery({
    queryKey: ["orders", orderId],
    queryFn: () => ordersService.get(orderId),
    enabled: Boolean(orderId),
  });

  const loadPlanQuery = useQuery({
    queryKey: ["planning", "load-plan", orderId],
    queryFn: () => planningService.getLoadPlan(orderId),
    enabled: Boolean(orderId),
    retry: false,
  });

  const trailersQuery = useQuery({
    queryKey: ["trailers"],
    queryFn: () => fleetService.listTrailers({ page: 1, page_size: 100, active: true }),
  });

  useEffect(() => {
    if (loadPlanQuery.data?.positions.length) {
      setPositions(loadPlanQuery.data.positions);
      return;
    }
    if (orderQuery.data) {
      setPositions(
        orderQuery.data.vehicles.map((vehicle, index) => ({
          vehicle_id: vehicle.id,
          vehicle_label: [vehicle.make, vehicle.model].filter(Boolean).join(" ") || vehicle.id.slice(0, 8),
          upper_deck: false,
          trailer_position: index + 1,
          loading_order: index + 1,
          unloading_order: orderQuery.data.vehicles.length - index,
          destination_city: null,
          height_m: null,
          weight_kg: null,
        })),
      );
    }
  }, [loadPlanQuery.data, orderQuery.data]);

  const trailer = useMemo(() => {
    const assignedId = orderQuery.data?.assigned_trailer_id;
    return trailersQuery.data?.items.find((item) => item.id === assignedId);
  }, [orderQuery.data, trailersQuery.data]);

  const capacity = trailer?.maximum_vehicle_count ?? Math.max(positions.length, 2);

  const saveMutation = useMutation({
    mutationFn: () =>
      planningService.saveLoadPlan({
        order_id: orderId,
        positions: positions.map((item) => ({
          vehicle_id: item.vehicle_id,
          upper_deck: item.upper_deck,
          trailer_position: item.trailer_position,
          loading_order: item.loading_order,
          unloading_order: item.unloading_order,
          destination_city: item.destination_city,
        })),
        acknowledge_warnings: Boolean(validation?.warnings.length),
      }),
    onSuccess: () => {
      setMessage("Loading plan draft saved.");
      queryClient.invalidateQueries({ queryKey: ["planning"] });
    },
  });

  const confirmMutation = useMutation({
    mutationFn: () =>
      planningService.saveLoadPlan({
        order_id: orderId,
        confirm: true,
        positions: positions.map((item) => ({
          vehicle_id: item.vehicle_id,
          upper_deck: item.upper_deck,
          trailer_position: item.trailer_position,
          loading_order: item.loading_order,
          unloading_order: item.unloading_order,
          destination_city: item.destination_city,
        })),
        acknowledge_warnings: true,
      }),
    onSuccess: () => {
      setMessage("Loading plan confirmed.");
      queryClient.invalidateQueries({ queryKey: ["planning"] });
    },
  });

  const handleMoveVehicle = (vehicleId: string, trailerPosition: number, upperDeck: boolean) => {
    setPositions((current) => {
      const moving = current.find((item) => item.vehicle_id === vehicleId);
      const displaced = current.find((item) => item.trailer_position === trailerPosition);
      if (!moving) return current;
      return current.map((item) => {
        if (item.vehicle_id === moving.vehicle_id) {
          return { ...item, trailer_position: trailerPosition, upper_deck: upperDeck };
        }
        if (displaced && item.vehicle_id === displaced.vehicle_id) {
          return { ...item, trailer_position: moving.trailer_position, upper_deck: moving.upper_deck };
        }
        return item;
      });
    });
  };

  const handleOptimized = (result: OptimizationResponse) => {
    const recommended = result.loading.positions as LoadingPositionDraft[];
    if (Array.isArray(recommended)) {
      setPositions(
        recommended.map((item) => ({
          vehicle_id: String(item.vehicle_id),
          vehicle_label: item.vehicle_label,
          upper_deck: Boolean(item.upper_deck),
          trailer_position: Number(item.trailer_position),
          loading_order: Number(item.loading_order),
          unloading_order: Number(item.unloading_order),
          destination_city: item.destination_city ?? null,
          height_m: item.height_m ?? null,
          weight_kg: item.weight_kg ?? null,
        })),
      );
    }
  };

  if (orderQuery.isLoading) return <LoadingState label="Loading order..." />;
  if (orderQuery.isError) return <ErrorAlert error={orderQuery.error} />;
  const order = orderQuery.data!;

  return (
    <Stack spacing={3}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <BoxTitle orderNumber={order.order_number} orderId={orderId} />
      </Stack>
      {message ? <Alert severity="success" onClose={() => setMessage(null)}>{message}</Alert> : null}
      {saveMutation.isError ? <ErrorAlert error={saveMutation.error} /> : null}
      {confirmMutation.isError ? <ErrorAlert error={confirmMutation.error} /> : null}

      <TrailerVisualization capacity={capacity} positions={positions} onMoveVehicle={handleMoveVehicle} />

      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <OptimizationPanel
          orderId={orderId}
          onOptimized={handleOptimized}
          onApproved={() => {
            setMessage("Optimization approved and applied.");
            queryClient.invalidateQueries({ queryKey: ["planning", "load-plan", orderId] });
          }}
        />
        <ValidationPanel orderId={orderId} positions={positions} onValidated={setValidation} />
      </Stack>

      <Stack direction="row" spacing={2}>
        <Button variant="outlined" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
          Save draft
        </Button>
        <Button variant="contained" onClick={() => confirmMutation.mutate()} disabled={confirmMutation.isPending}>
          Confirm plan
        </Button>
        <Button component={RouterLink} to="/planning" variant="text">
          Back to planning board
        </Button>
      </Stack>
    </Stack>
  );
}

function BoxTitle({ orderNumber, orderId }: { orderNumber: string; orderId: string }) {
  return (
    <Stack spacing={0.5}>
      <Typography variant="h4" fontWeight={700}>
        Loading board · {orderNumber}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Order {orderId.slice(0, 8)} · drag vehicles to adjust positions before confirmation
      </Typography>
    </Stack>
  );
}
