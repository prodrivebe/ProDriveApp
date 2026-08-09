import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import type { LoadingPositionDraft } from "../types/api";
import { buildSlots } from "./trailerVisualizationUtils";

interface TrailerVisualizationProps {
  capacity: number;
  positions: LoadingPositionDraft[];
  onMoveVehicle: (vehicleId: string, trailerPosition: number, upperDeck: boolean) => void;
}

function SlotCard({
  slot,
  occupied,
  onDropVehicle,
}: {
  slot: { position: number; upperDeck: boolean };
  occupied: LoadingPositionDraft | undefined;
  onDropVehicle: (vehicleId: string, position: number, upperDeck: boolean) => void;
}) {
  return (
    <Card
      variant="outlined"
      sx={{ minHeight: 96, bgcolor: slot.upperDeck ? "info.50" : "grey.50" }}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        const vehicleId = event.dataTransfer.getData("vehicleId");
        if (vehicleId) onDropVehicle(vehicleId, slot.position, slot.upperDeck);
      }}
    >
      <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
        <Typography variant="caption" color="text.secondary">
          {slot.upperDeck ? "Upper" : "Lower"} #{slot.position}
        </Typography>
        {occupied ? (
          <Box
            draggable
            onDragStart={(event) => event.dataTransfer.setData("vehicleId", occupied.vehicle_id)}
          >
            <Typography variant="subtitle2" fontWeight={700}>
              {occupied.vehicle_label ?? occupied.vehicle_id.slice(0, 8)}
            </Typography>
            <Typography variant="caption" display="block">
              Load {occupied.loading_order} · Unload {occupied.unloading_order}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {occupied.destination_city ?? "—"} · {occupied.height_m ?? "?"}m · {occupied.weight_kg ?? "?"}kg
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Drop vehicle
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

export function TrailerVisualization({ capacity, positions, onMoveVehicle }: TrailerVisualizationProps) {
  const { lower, upper } = buildSlots(capacity);
  const byPosition = new Map(positions.map((item) => [item.trailer_position, item]));

  return (
    <Stack spacing={2}>
      <Alert severity="info">
        Drag vehicles between deck slots. Upper deck accepts shorter vehicles; positions sync with loading order.
      </Alert>
      {upper.length ? (
        <Box>
          <Typography variant="subtitle1" fontWeight={700} gutterBottom>
            Upper deck
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {upper.map((slot) => (
              <Box key={`upper-${slot.position}`} sx={{ width: 180 }}>
                <SlotCard
                  slot={slot}
                  occupied={byPosition.get(slot.position)}
                  onDropVehicle={onMoveVehicle}
                />
              </Box>
            ))}
          </Stack>
        </Box>
      ) : null}
      <Box>
        <Typography variant="subtitle1" fontWeight={700} gutterBottom>
          Lower deck
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {lower.map((slot) => (
            <Box key={`lower-${slot.position}`} sx={{ width: 180 }}>
              <SlotCard
                slot={slot}
                occupied={byPosition.get(slot.position)}
                onDropVehicle={onMoveVehicle}
              />
            </Box>
          ))}
        </Stack>
      </Box>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        {positions.map((item) => (
          <Chip
            key={item.vehicle_id}
            label={`${item.vehicle_label ?? item.vehicle_id.slice(0, 8)} → pos ${item.trailer_position}`}
            size="small"
          />
        ))}
      </Stack>
    </Stack>
  );
}
