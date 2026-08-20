import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
} from "@mui/material";
import type { Truck, TruckCreatePayload, TruckUpdatePayload } from "../types/api";

const truckSchema = z.object({
  registration_number: z.string().min(1, "Registration number is required"),
  brand: z.string().optional(),
  model: z.string().optional(),
  vin: z.string().optional(),
  capacity: z.string().optional(),
  current_mileage: z.string().optional(),
  active: z.boolean(),
});

type TruckFormValues = z.infer<typeof truckSchema>;

interface TruckFormDialogProps {
  open: boolean;
  truck?: Truck | null;
  onClose: () => void;
  onSubmit: (payload: TruckCreatePayload | TruckUpdatePayload) => Promise<void>;
  isSubmitting?: boolean;
}

function toFormValues(truck?: Truck | null): TruckFormValues {
  return {
    registration_number: truck?.registration_number ?? "",
    brand: truck?.brand ?? "",
    model: truck?.model ?? "",
    vin: truck?.vin ?? "",
    capacity: truck?.capacity != null ? String(truck.capacity) : "",
    current_mileage: truck?.current_mileage != null ? String(truck.current_mileage) : "",
    active: truck?.active ?? true,
  };
}

function parseOptionalInt(value: string | undefined): number | null {
  const trimmed = value?.trim();
  if (!trimmed) return null;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

function toPayload(values: TruckFormValues, isEdit: boolean): TruckCreatePayload | TruckUpdatePayload {
  const base = {
    registration_number: values.registration_number.trim(),
    brand: values.brand?.trim() || null,
    model: values.model?.trim() || null,
    vin: values.vin?.trim() || null,
    capacity: parseOptionalInt(values.capacity),
    active: values.active,
  };

  if (isEdit) {
    return {
      ...base,
      current_mileage: parseOptionalInt(values.current_mileage),
    };
  }

  return base;
}

export function TruckFormDialog({
  open,
  truck,
  onClose,
  onSubmit,
  isSubmitting = false,
}: TruckFormDialogProps) {
  const isEdit = Boolean(truck);
  const form = useForm<TruckFormValues>({
    resolver: zodResolver(truckSchema),
    defaultValues: toFormValues(truck),
  });

  useEffect(() => {
    if (open) {
      form.reset(toFormValues(truck));
    }
  }, [open, truck, form]);

  const handleSubmit = form.handleSubmit(async (values) => {
    await onSubmit(toPayload(values, isEdit));
  });

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{isEdit ? "Edit truck" : "Add truck"}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField
            label="Registration number"
            fullWidth
            required
            error={Boolean(form.formState.errors.registration_number)}
            helperText={form.formState.errors.registration_number?.message}
            {...form.register("registration_number")}
          />
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <TextField label="Brand" fullWidth {...form.register("brand")} />
            <TextField label="Model" fullWidth {...form.register("model")} />
          </Stack>
          <TextField label="VIN" fullWidth {...form.register("vin")} />
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <TextField label="Capacity" type="number" fullWidth {...form.register("capacity")} />
            {isEdit ? (
              <TextField
                label="Current mileage (km)"
                type="number"
                fullWidth
                {...form.register("current_mileage")}
              />
            ) : null}
          </Stack>
          <FormControlLabel
            control={
              <Switch
                checked={form.watch("active")}
                onChange={(e) => form.setValue("active", e.target.checked)}
              />
            }
            label="Active truck"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : isEdit ? "Save changes" : "Create truck"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
