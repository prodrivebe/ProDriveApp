import { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
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
  TextField,
  Typography,
} from "@mui/material";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
import { useMutation } from "@tanstack/react-query";
import { aiService } from "../services/aiService";
import { ConfidenceChip } from "./ConfidenceChip";
import { ErrorAlert } from "./ErrorAlert";
import type { AISuggestion, Customer, OrderParseOutput, OrderParseTableRow } from "../types/api";
import {
  applyTableRowsToOutput,
  buildTableRows,
  collectParseValidationMessages,
} from "../utils/orderParseOutput";

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
  const [tableRows, setTableRows] = useState<OrderParseTableRow[]>([]);
  const [rejectReason, setRejectReason] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);

  const parseMutation = useMutation({
    mutationFn: () => aiService.parseOrder(message),
    onSuccess: (data) => {
      const parsed = asParseOutput(data.output_json);
      setSuggestion(data);
      setEditedOutput(parsed);
      setTableRows(buildTableRows(parsed));
      setConfirmOpen(false);
    },
  });

  const approveMutation = useMutation({
    mutationFn: () => {
      const outputWithRows = applyTableRowsToOutput(editedOutput!, tableRows);
      return aiService.approveSuggestion(suggestion!.id, {
        customer_id: customerId,
        edited_output: outputWithRows as Record<string, unknown>,
      });
    },
    onSuccess: (data) => {
      const orderId = (data.output_json as OrderParseOutput).created_order_id;
      setConfirmOpen(false);
      if (orderId) onOrderCreated(orderId);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => aiService.rejectSuggestion(suggestion!.id, rejectReason || undefined),
    onSuccess: (data) => setSuggestion(data),
  });

  const output = editedOutput;
  const confidence = output?.field_confidence ?? {};
  const validation = useMemo(
    () => (output ? collectParseValidationMessages(output) : { errors: [], warnings: [], vehicleCount: 0 }),
    [output],
  );

  const updateTableRow = (index: number, field: keyof OrderParseTableRow, value: string | boolean) => {
    setTableRows((rows) => {
      const next = [...rows];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const syncRowsToOutput = (rows: OrderParseTableRow[]) => {
    if (!output) return;
    setEditedOutput(applyTableRowsToOutput(output, rows));
  };

  const handleApproveClick = () => {
    syncRowsToOutput(tableRows);
    setConfirmOpen(true);
  };

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
                {Math.round(suggestion.confidence * 100)}% · {validation.vehicleCount} vehicle
                {validation.vehicleCount === 1 ? "" : "s"}
              </Alert>

              {validation.errors.length > 0 ? (
                <Alert severity="error">
                  {validation.errors.map((item) => (
                    <Typography key={item} variant="body2">
                      {item}
                    </Typography>
                  ))}
                </Alert>
              ) : null}

              {validation.warnings.length > 0 ? (
                <Alert severity="warning">
                  {validation.warnings.map((item) => (
                    <Typography key={item} variant="body2">
                      {item}
                    </Typography>
                  ))}
                </Alert>
              ) : null}

              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <ConfidenceChip label="Customer" confidence={confidence.customer_name} />
                <ConfidenceChip label="Pickup" confidence={confidence.pickup} />
                <ConfidenceChip label="Delivery" confidence={confidence.delivery} />
                <ConfidenceChip label="Vehicles" confidence={confidence.vehicles} />
                <ConfidenceChip label="VIN" confidence={confidence.vin} />
                <ConfidenceChip label="Autohero" confidence={confidence.autohero_stock} />
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

              {tableRows.length > 0 ? (
                <Box sx={{ overflowX: "auto" }}>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Parsed vehicles
                  </Typography>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Stock ID</TableCell>
                        <TableCell>VIN</TableCell>
                        <TableCell>Model</TableCell>
                        <TableCell>License plate</TableCell>
                        <TableCell>Location</TableCell>
                        <TableCell>LL ID</TableCell>
                        <TableCell>Autohero</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {tableRows.map((row, index) => (
                        <TableRow key={`row-${index}`}>
                          <TableCell>
                            <TextField
                              size="small"
                              value={row.stock_id ?? ""}
                              onChange={(e) => updateTableRow(index, "stock_id", e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              value={row.vin ?? ""}
                              onChange={(e) => updateTableRow(index, "vin", e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              value={row.model ?? ""}
                              onChange={(e) => updateTableRow(index, "model", e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              value={row.license_plate ?? ""}
                              onChange={(e) => updateTableRow(index, "license_plate", e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              value={row.location ?? ""}
                              onChange={(e) => updateTableRow(index, "location", e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              value={row.ll_id ?? ""}
                              onChange={(e) => updateTableRow(index, "ll_id", e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            <Checkbox
                              checked={Boolean(row.autohero_car)}
                              onChange={(e) => updateTableRow(index, "autohero_car", e.target.checked)}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Box>
              ) : null}

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

                  {confirmOpen ? (
                    <Alert severity="warning">
                      Confirm creation of order with {tableRows.length || validation.vehicleCount} vehicle
                      {(tableRows.length || validation.vehicleCount) === 1 ? "" : "s"} for the selected
                      customer?
                    </Alert>
                  ) : null}

                  <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
                    {!confirmOpen ? (
                      <Button
                        variant="contained"
                        color="success"
                        onClick={handleApproveClick}
                        disabled={!customerId}
                      >
                        Review &amp; confirm
                      </Button>
                    ) : (
                      <>
                        <Button
                          variant="contained"
                          color="success"
                          onClick={() => approveMutation.mutate()}
                          disabled={!customerId || approveMutation.isPending}
                        >
                          {approveMutation.isPending ? "Creating order..." : "Approve & create order"}
                        </Button>
                        <Button variant="outlined" onClick={() => setConfirmOpen(false)}>
                          Back to edit
                        </Button>
                      </>
                    )}
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
