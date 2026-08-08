import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
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
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from "@mui/material";
import { apiGetList, apiPost } from "../services/apiClient";
import type { Customer, OrderDetail, ParsedOrderDraft } from "../types/api";

const steps = ["Customer", "Order details", "Review"];

export function CreateOrderPage() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerId, setCustomerId] = useState("");
  const [messageText, setMessageText] = useState("");
  const [pickupCity, setPickupCity] = useState("");
  const [deliveryCity, setDeliveryCity] = useState("");
  const [vehicleMake, setVehicleMake] = useState("");
  const [vehicleModel, setVehicleModel] = useState("");
  const [notes, setNotes] = useState("");
  const [draft, setDraft] = useState<ParsedOrderDraft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadCustomers = async () => {
      const result = await apiGetList<Customer>("/customers?page=1&page_size=100");
      setCustomers(result.items);
    };
    void loadCustomers();
  }, []);

  const parseMessage = async () => {
    if (!messageText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const parsed = await apiPost<ParsedOrderDraft>("/ai/parse-order", {
        message: messageText,
      });
      setDraft(parsed);
      if (parsed.pickup_stops[0]?.city) {
        setPickupCity(parsed.pickup_stops[0].city);
      }
      if (parsed.delivery_stops[0]?.city) {
        setDeliveryCity(parsed.delivery_stops[0].city);
      }
      if (parsed.vehicles[0]?.make) {
        setVehicleMake(parsed.vehicles[0].make);
      }
      if (parsed.vehicles[0]?.model) {
        setVehicleModel(parsed.vehicles[0].model);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI parse failed.");
    } finally {
      setLoading(false);
    }
  };

  const createOrder = async () => {
    if (!customerId) {
      setError("Select a customer.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const order = await apiPost<OrderDetail>("/orders", {
        customer_id: customerId,
        notes: notes || null,
        stops: [
          ...(pickupCity
            ? [{ stop_type: "PICKUP", sequence: 1, city: pickupCity }]
            : []),
          ...(deliveryCity
            ? [{ stop_type: "DELIVERY", sequence: 2, city: deliveryCity }]
            : []),
        ],
        vehicles: [
          ...(vehicleMake || vehicleModel
            ? [{ make: vehicleMake || null, model: vehicleModel || null }]
            : []),
        ],
      });
      navigate(`/orders/${order.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create order failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Create order
      </Typography>

      <Stepper activeStep={activeStep}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error ? <Alert severity="error">{error}</Alert> : null}

      {activeStep === 0 ? (
        <Card>
          <CardContent>
            <FormControl fullWidth>
              <InputLabel>Customer</InputLabel>
              <Select
                value={customerId}
                label="Customer"
                onChange={(e) => setCustomerId(e.target.value)}
              >
                {customers.map((customer) => (
                  <MenuItem key={customer.id} value={customer.id}>
                    {customer.company_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Box sx={{ mt: 2, display: "flex", justifyContent: "flex-end" }}>
              <Button variant="contained" onClick={() => setActiveStep(1)} disabled={!customerId}>
                Next
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : null}

      {activeStep === 1 ? (
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <TextField
                label="Paste customer message (optional)"
                multiline
                minRows={4}
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                fullWidth
              />
              <Button variant="outlined" onClick={parseMessage} disabled={loading}>
                Extract with AI
              </Button>
              {draft ? (
                <Alert severity="info">
                  AI confidence: {(draft.confidence_score * 100).toFixed(0)}%
                </Alert>
              ) : null}
              <TextField label="Pickup city" value={pickupCity} onChange={(e) => setPickupCity(e.target.value)} fullWidth />
              <TextField label="Delivery city" value={deliveryCity} onChange={(e) => setDeliveryCity(e.target.value)} fullWidth />
              <TextField label="Vehicle make" value={vehicleMake} onChange={(e) => setVehicleMake(e.target.value)} fullWidth />
              <TextField label="Vehicle model" value={vehicleModel} onChange={(e) => setVehicleModel(e.target.value)} fullWidth />
              <TextField label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} fullWidth />
            </Stack>
            <Box sx={{ mt: 2, display: "flex", justifyContent: "space-between" }}>
              <Button onClick={() => setActiveStep(0)}>Back</Button>
              <Button variant="contained" onClick={() => setActiveStep(2)}>
                Next
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : null}

      {activeStep === 2 ? (
        <Card>
          <CardContent>
            <Typography gutterBottom>
              Customer: {customers.find((c) => c.id === customerId)?.company_name}
            </Typography>
            <Typography gutterBottom>Pickup: {pickupCity || "—"}</Typography>
            <Typography gutterBottom>Delivery: {deliveryCity || "—"}</Typography>
            <Typography gutterBottom>
              Vehicle: {[vehicleMake, vehicleModel].filter(Boolean).join(" ") || "—"}
            </Typography>
            <Box sx={{ mt: 2, display: "flex", justifyContent: "space-between" }}>
              <Button onClick={() => setActiveStep(1)}>Back</Button>
              <Button variant="contained" onClick={createOrder} disabled={loading}>
                Create order
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : null}
    </Stack>
  );
}
