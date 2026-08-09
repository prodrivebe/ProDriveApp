import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import { useMutation, useQuery } from "@tanstack/react-query";
import { customersService } from "../services/customersService";
import { driversService } from "../services/driversService";
import { fleetService } from "../services/fleetService";
import { ordersService } from "../services/ordersService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { AiOrderPanel } from "../components/AiOrderPanel";
import { getErrorMessage } from "../utils/errors";

const stopSchema = z.object({
  stop_type: z.enum(["PICKUP", "DELIVERY"]),
  sequence: z.number().min(1),
  city: z.string().optional(),
  address: z.string().optional(),
  country: z.string().optional(),
});

const vehicleSchema = z.object({
  make: z.string().optional(),
  model: z.string().optional(),
  vin: z.string().max(17).optional(),
});

const createOrderSchema = z.object({
  customer_id: z.string().min(1, "Select a customer"),
  planned_pickup_date: z.string().optional(),
  planned_delivery_date: z.string().optional(),
  notes: z.string().optional(),
  driver_id: z.string().optional(),
  truck_id: z.string().optional(),
  trailer_id: z.string().optional(),
  pickup_stops: z.array(stopSchema).min(1, "Add at least one pickup stop"),
  delivery_stops: z.array(stopSchema).min(1, "Add at least one delivery stop"),
  vehicles: z.array(vehicleSchema).min(1, "Add at least one vehicle"),
});

type CreateOrderForm = z.infer<typeof createOrderSchema>;

export function CreateOrderPage() {
  const navigate = useNavigate();
  const customersQuery = useQuery({
    queryKey: ["customers"],
    queryFn: () => customersService.list({ page: 1, page_size: 200 }),
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

  const form = useForm<CreateOrderForm>({
    resolver: zodResolver(createOrderSchema),
    defaultValues: {
      pickup_stops: [{ stop_type: "PICKUP", sequence: 1, city: "" }],
      delivery_stops: [{ stop_type: "DELIVERY", sequence: 1, city: "" }],
      vehicles: [{ make: "", model: "" }],
    },
  });

  const pickupFields = useFieldArray({ control: form.control, name: "pickup_stops" });
  const deliveryFields = useFieldArray({ control: form.control, name: "delivery_stops" });
  const vehicleFields = useFieldArray({ control: form.control, name: "vehicles" });

  const createMutation = useMutation({
    mutationFn: async (values: CreateOrderForm) => {
      const stops = [
        ...values.pickup_stops.map((stop, index) => ({
          ...stop,
          stop_type: "PICKUP" as const,
          sequence: index + 1,
        })),
        ...values.delivery_stops.map((stop, index) => ({
          ...stop,
          stop_type: "DELIVERY" as const,
          sequence: index + 1,
        })),
      ];
      const order = await ordersService.create({
        customer_id: values.customer_id,
        planned_pickup_date: values.planned_pickup_date || null,
        planned_delivery_date: values.planned_delivery_date || null,
        notes: values.notes || null,
        stops,
        vehicles: values.vehicles,
      });
      if (values.driver_id) {
        await ordersService.assignDriver(order.id, {
          driver_id: values.driver_id,
          truck_id: values.truck_id || null,
          trailer_id: values.trailer_id || null,
        });
      }
      return order;
    },
    onSuccess: (order) => navigate(`/orders/${order.id}`),
  });

  if (customersQuery.isLoading) return <LoadingState />;

  const onSubmit = form.handleSubmit((values) => createMutation.mutate(values));

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Create order
      </Typography>
      {createMutation.isError ? <ErrorAlert error={createMutation.error} /> : null}
      {createMutation.isSuccess ? <Alert severity="success">Order created successfully.</Alert> : null}

      <AiOrderPanel
        customers={customersQuery.data?.items ?? []}
        onOrderCreated={(orderId) => navigate(`/orders/${orderId}`)}
      />

      <Box component="form" onSubmit={onSubmit}>
        <Stack spacing={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Customer & schedule
              </Typography>
              <Stack spacing={2}>
                <FormControl fullWidth error={Boolean(form.formState.errors.customer_id)}>
                  <InputLabel>Customer</InputLabel>
                  <Select
                    label="Customer"
                    value={form.watch("customer_id") ?? ""}
                    onChange={(e) => form.setValue("customer_id", e.target.value)}
                  >
                    {customersQuery.data?.items.map((customer) => (
                      <MenuItem key={customer.id} value={customer.id}>
                        {customer.company_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                  <TextField
                    label="Planned pickup"
                    type="date"
                    InputLabelProps={{ shrink: true }}
                    fullWidth
                    {...form.register("planned_pickup_date")}
                  />
                  <TextField
                    label="Planned delivery"
                    type="date"
                    InputLabelProps={{ shrink: true }}
                    fullWidth
                    {...form.register("planned_delivery_date")}
                  />
                </Stack>
                <TextField label="Notes" multiline minRows={3} fullWidth {...form.register("notes")} />
              </Stack>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Pickup stops
              </Typography>
              {pickupFields.fields.map((field, index) => (
                <Stack key={field.id} direction="row" spacing={1} sx={{ mb: 1 }}>
                  <TextField label="City" fullWidth {...form.register(`pickup_stops.${index}.city`)} />
                  <TextField label="Address" fullWidth {...form.register(`pickup_stops.${index}.address`)} />
                  <IconButton onClick={() => pickupFields.remove(index)} disabled={pickupFields.fields.length === 1}>
                    <DeleteIcon />
                  </IconButton>
                </Stack>
              ))}
              <Button startIcon={<AddIcon />} onClick={() => pickupFields.append({ stop_type: "PICKUP", sequence: pickupFields.fields.length + 1 })}>
                Add pickup
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Delivery stops
              </Typography>
              {deliveryFields.fields.map((field, index) => (
                <Stack key={field.id} direction="row" spacing={1} sx={{ mb: 1 }}>
                  <TextField label="City" fullWidth {...form.register(`delivery_stops.${index}.city`)} />
                  <TextField label="Address" fullWidth {...form.register(`delivery_stops.${index}.address`)} />
                  <IconButton onClick={() => deliveryFields.remove(index)} disabled={deliveryFields.fields.length === 1}>
                    <DeleteIcon />
                  </IconButton>
                </Stack>
              ))}
              <Button startIcon={<AddIcon />} onClick={() => deliveryFields.append({ stop_type: "DELIVERY", sequence: deliveryFields.fields.length + 1 })}>
                Add delivery
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Vehicles
              </Typography>
              {vehicleFields.fields.map((field, index) => (
                <Stack key={field.id} direction={{ xs: "column", md: "row" }} spacing={1} sx={{ mb: 1 }}>
                  <TextField label="Make" fullWidth {...form.register(`vehicles.${index}.make`)} />
                  <TextField label="Model" fullWidth {...form.register(`vehicles.${index}.model`)} />
                  <TextField label="VIN" fullWidth {...form.register(`vehicles.${index}.vin`)} />
                  <IconButton onClick={() => vehicleFields.remove(index)} disabled={vehicleFields.fields.length === 1}>
                    <DeleteIcon />
                  </IconButton>
                </Stack>
              ))}
              <Button startIcon={<AddIcon />} onClick={() => vehicleFields.append({ make: "", model: "" })}>
                Add vehicle
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Assignment
              </Typography>
              <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                <FormControl fullWidth>
                  <InputLabel>Driver</InputLabel>
                  <Select label="Driver" value={form.watch("driver_id") ?? ""} onChange={(e) => form.setValue("driver_id", e.target.value)}>
                    <MenuItem value="">Unassigned</MenuItem>
                    {driversQuery.data?.items.map((driver) => (
                      <MenuItem key={driver.id} value={driver.id}>
                        {driver.phone ?? driver.id.slice(0, 8)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl fullWidth>
                  <InputLabel>Truck</InputLabel>
                  <Select label="Truck" value={form.watch("truck_id") ?? ""} onChange={(e) => form.setValue("truck_id", e.target.value)}>
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
                  <Select label="Trailer" value={form.watch("trailer_id") ?? ""} onChange={(e) => form.setValue("trailer_id", e.target.value)}>
                    <MenuItem value="">None</MenuItem>
                    {trailersQuery.data?.items.map((trailer) => (
                      <MenuItem key={trailer.id} value={trailer.id}>
                        {trailer.registration_number}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Stack>
            </CardContent>
          </Card>

          <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 2 }}>
            <Button onClick={() => navigate("/orders")}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create order"}
            </Button>
          </Box>
          {form.formState.errors.root ? (
            <Alert severity="error">{getErrorMessage(form.formState.errors.root)}</Alert>
          ) : null}
        </Stack>
      </Box>
    </Stack>
  );
}
