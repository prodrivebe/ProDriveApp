import { Alert, Button, Card, CardContent, List, ListItem, ListItemText, Stack, Typography } from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { planningService } from "../services/planningService";
import { ErrorAlert } from "./ErrorAlert";
import type { LoadingPositionDraft, ValidationResponse } from "../types/api";

interface ValidationPanelProps {
  orderId: string;
  positions: LoadingPositionDraft[];
  onValidated: (result: ValidationResponse) => void;
}

export function ValidationPanel({ orderId, positions, onValidated }: ValidationPanelProps) {
  const validateMutation = useMutation({
    mutationFn: () =>
      planningService.validate({
        order_id: orderId,
        positions: positions.map((item) => ({
          vehicle_id: item.vehicle_id,
          upper_deck: item.upper_deck,
          trailer_position: item.trailer_position,
          loading_order: item.loading_order,
          unloading_order: item.unloading_order,
          destination_city: item.destination_city,
        })),
      }),
    onSuccess: onValidated,
  });

  const result = validateMutation.data;

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6">Capacity validation</Typography>
          <Button variant="outlined" onClick={() => validateMutation.mutate()} disabled={validateMutation.isPending}>
            {validateMutation.isPending ? "Validating..." : "Validate plan"}
          </Button>
          {validateMutation.isError ? <ErrorAlert error={validateMutation.error} /> : null}
          {result ? (
            <Stack spacing={1}>
              <Alert severity={result.is_valid ? "success" : "error"}>
                {result.is_valid ? "Plan is valid" : "Validation failed"}
              </Alert>
              <Typography variant="body2">
                Height {result.estimated_total_height_m}m · Weight {result.estimated_total_weight_kg}kg · Axles{" "}
                {result.front_axle_percent}/{result.rear_axle_percent}
              </Typography>
              {[...result.errors, ...result.warnings].length ? (
                <List dense>
                  {[...result.errors, ...result.warnings].map((item) => (
                    <ListItem key={`${item.code}-${item.message}`} disablePadding>
                      <ListItemText primary={`${item.severity ?? "error"}: ${item.message}`} />
                    </ListItem>
                  ))}
                </List>
              ) : null}
            </Stack>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}
