import { useState } from "react";
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
  TextField,
  Typography,
} from "@mui/material";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
import { useMutation } from "@tanstack/react-query";
import { aiService } from "../services/aiService";
import { ConfidenceChip } from "./ConfidenceChip";
import { ErrorAlert } from "./ErrorAlert";
import type { AISuggestion, Customer, OrderParseOutput } from "../types/api";

interface AiOrderPanelProps {
  customers: Customer[];
  onOrderCreated: (orderId: string) => void;
}

function asParseOutput(output: Record<string, unknown>): OrderParseOutput {
  return output as OrderParseOutput;
}

export function AiOrderPanel({ customers, onOrderCreated }: AiOrderPanelProps) {
  const [message, setMessage] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [suggestion, setSuggestion] = useState<AISuggestion | null>(null);
  const [editedOutput, setEditedOutput] = useState<OrderParseOutput | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const parseMutation = useMutation({
    mutationFn: () => aiService.parseOrder(message),
    onSuccess: (data) => {
      setSuggestion(data);
      setEditedOutput(asParseOutput(data.output_json));
    },
  });

  const approveMutation = useMutation({
    mutationFn: () =>
      aiService.approveSuggestion(suggestion!.id, {
        customer_id: customerId,
        edited_output: editedOutput as Record<string, unknown>,
      }),
    onSuccess: (data) => {
      const orderId = (data.output_json as OrderParseOutput).created_order_id;
      if (orderId) onOrderCreated(orderId);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => aiService.rejectSuggestion(suggestion!.id, rejectReason || undefined),
    onSuccess: (data) => setSuggestion(data),
  });

  const output = editedOutput;
  const confidence = output?.field_confidence ?? {};

  const updatePickupCity = (index: number, city: string) => {
    if (!output) return;
    const pickupStops = [...(output.pickup_stops ?? [])];
    pickupStops[index] = { ...pickupStops[index], city };
    setEditedOutput({ ...output, pickup_stops: pickupStops });
  };

  const updateDeliveryCity = (index: number, city: string) => {
    if (!output) return;
    const deliveryStops = [...(output.delivery_stops ?? [])];
    deliveryStops[index] = { ...deliveryStops[index], city };
    setEditedOutput({ ...output, delivery_stops: deliveryStops });
  };

  const updateVehicle = (index: number, field: "make" | "model" | "vin", value: string) => {
    if (!output) return;
    const vehicles = [...(output.vehicles ?? [])];
    vehicles[index] = { ...vehicles[index], [field]: value };
    setEditedOutput({ ...output, vehicles });
  };

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} alignItems="center">
            <AutoFixHighIcon color="primary" />
            <Typography variant="h6">AI order assistant</Typography>
          </Stack>
          <Typography color="text.secondary" variant="body2">
            Paste a customer email or message. AI extracts order details for your review — nothing is
            created until you approve.
          </Typography>

          <TextField
            label="Customer message"
            multiline
            minRows={4}
            fullWidth
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={"Customer: ACME Logistics\nPick up:\nBMW X5\nAmsterdam\nDeliver:\nBrussels"}
          />

          <Box>
            <Button
              variant="contained"
              onClick={() => parseMutation.mutate()}
              disabled={!message.trim() || parseMutation.isPending}
            >
              {parseMutation.isPending ? "Parsing..." : "Parse order"}
            </Button>
          </Box>

          {parseMutation.isError ? <ErrorAlert error={parseMutation.error} /> : null}

          {suggestion && output ? (
            <Stack spacing={2}>
              <Alert severity="info">
                Suggestion {suggestion.status.toLowerCase()} · overall confidence{" "}
                {Math.round(suggestion.confidence * 100)}%
              </Alert>

              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <ConfidenceChip label="Customer" confidence={confidence.customer_name} />
                <ConfidenceChip label="Pickup" confidence={confidence.pickup} />
                <ConfidenceChip label="Delivery" confidence={confidence.delivery} />
                <ConfidenceChip label="Vehicles" confidence={confidence.vehicles} />
                <ConfidenceChip label="VIN" confidence={confidence.vin} />
                <ConfidenceChip label="Pickup date" confidence={confidence.planned_pickup_date} />
              </Stack>

              <TextField
                label="Extracted customer name"
                fullWidth
                value={output.customer_name ?? ""}
                onChange={(e) => setEditedOutput({ ...output, customer_name: e.target.value })}
                helperText={
                  (confidence.customer_name ?? 0) < 0.7
                    ? "Low confidence — verify before approving"
                    : undefined
                }
              />

              {(output.pickup_stops ?? []).map((stop, index) => (
                <TextField
                  key={`pickup-${index}`}
                  label={`Pickup city ${index + 1}`}
                  fullWidth
                  value={stop.city ?? ""}
                  onChange={(e) => updatePickupCity(index, e.target.value)}
                />
              ))}

              {(output.delivery_stops ?? []).map((stop, index) => (
                <TextField
                  key={`delivery-${index}`}
                  label={`Delivery city ${index + 1}`}
                  fullWidth
                  value={stop.city ?? ""}
                  onChange={(e) => updateDeliveryCity(index, e.target.value)}
                />
              ))}

              {(output.vehicles ?? []).map((vehicle, index) => (
                <Stack key={`vehicle-${index}`} direction={{ xs: "column", md: "row" }} spacing={1}>
                  <TextField
                    label="Make"
                    fullWidth
                    value={vehicle.make ?? ""}
                    onChange={(e) => updateVehicle(index, "make", e.target.value)}
                  />
                  <TextField
                    label="Model"
                    fullWidth
                    value={vehicle.model ?? ""}
                    onChange={(e) => updateVehicle(index, "model", e.target.value)}
                  />
                  <TextField
                    label="VIN"
                    fullWidth
                    value={vehicle.vin ?? ""}
                    onChange={(e) => updateVehicle(index, "vin", e.target.value)}
                    helperText={
                      (confidence.vin ?? 0) < 0.7 ? "Low confidence VIN — verify manually" : undefined
                    }
                  />
                </Stack>
              ))}

              <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                <TextField
                  label="Planned pickup"
                  type="date"
                  InputLabelProps={{ shrink: true }}
                  fullWidth
                  value={output.planned_pickup_date ?? ""}
                  onChange={(e) =>
                    setEditedOutput({ ...output, planned_pickup_date: e.target.value || null })
                  }
                />
                <TextField
                  label="Planned delivery"
                  type="date"
                  InputLabelProps={{ shrink: true }}
                  fullWidth
                  value={output.planned_delivery_date ?? ""}
                  onChange={(e) =>
                    setEditedOutput({ ...output, planned_delivery_date: e.target.value || null })
                  }
                />
              </Stack>

              <TextField
                label="Notes"
                multiline
                minRows={2}
                fullWidth
                value={output.notes ?? ""}
                onChange={(e) => setEditedOutput({ ...output, notes: e.target.value })}
              />

              {suggestion.status === "PENDING" ? (
                <>
                  <FormControl fullWidth>
                    <InputLabel>Customer for order</InputLabel>
                    <Select
                      label="Customer for order"
                      value={customerId}
                      onChange={(e) => setCustomerId(e.target.value)}
                    >
                      {customers.map((customer) => (
                        <MenuItem key={customer.id} value={customer.id}>
                          {customer.company_name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="contained"
                      color="success"
                      onClick={() => approveMutation.mutate()}
                      disabled={!customerId || approveMutation.isPending}
                    >
                      {approveMutation.isPending ? "Creating order..." : "Approve & create order"}
                    </Button>
                    <TextField
                      label="Rejection reason"
                      size="small"
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                    />
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={() => rejectMutation.mutate()}
                      disabled={rejectMutation.isPending}
                    >
                      Reject
                    </Button>
                  </Stack>
                </>
              ) : null}

              {approveMutation.isError ? <ErrorAlert error={approveMutation.error} /> : null}
              {rejectMutation.isError ? <ErrorAlert error={rejectMutation.error} /> : null}
              {suggestion.status === "APPROVED" ? (
                <Alert severity="success">Suggestion approved. Order created.</Alert>
              ) : null}
              {suggestion.status === "REJECTED" ? (
                <Alert severity="warning">Suggestion rejected and logged for audit.</Alert>
              ) : null}
            </Stack>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}
