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
  Typography,
} from "@mui/material";
import type { Customer, CustomerCreatePayload } from "../types/api";

const customerSchema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  vat_number: z.string().optional(),
  street: z.string().optional(),
  house_number: z.string().optional(),
  postal_code: z.string().optional(),
  address: z.string().optional(),
  city: z.string().optional(),
  country: z.string().optional(),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  invoice_email: z.string().email("Invalid invoice email").optional().or(z.literal("")),
  phone: z.string().optional(),
  dispatch_phone: z.string().optional(),
  is_active: z.boolean(),
  notes: z.string().optional(),
});

type CustomerFormValues = z.infer<typeof customerSchema>;

interface CustomerFormDialogProps {
  open: boolean;
  customer?: Customer | null;
  onClose: () => void;
  onSubmit: (payload: CustomerCreatePayload) => Promise<void>;
  isSubmitting?: boolean;
}

function toFormValues(customer?: Customer | null): CustomerFormValues {
  return {
    company_name: customer?.company_name ?? "",
    vat_number: customer?.vat_number ?? "",
    street: customer?.street ?? "",
    house_number: customer?.house_number ?? "",
    postal_code: customer?.postal_code ?? "",
    address: customer?.address ?? "",
    city: customer?.city ?? "",
    country: customer?.country ?? "",
    email: customer?.email ?? "",
    invoice_email: customer?.invoice_email ?? "",
    phone: customer?.phone ?? "",
    dispatch_phone: customer?.dispatch_phone ?? "",
    is_active: customer?.is_active ?? true,
    notes: customer?.notes ?? "",
  };
}

function toPayload(values: CustomerFormValues): CustomerCreatePayload {
  const optional = (value: string | undefined) => value?.trim() || null;
  return {
    company_name: values.company_name.trim(),
    vat_number: optional(values.vat_number),
    street: optional(values.street),
    house_number: optional(values.house_number),
    postal_code: optional(values.postal_code),
    address: optional(values.address),
    city: optional(values.city),
    country: optional(values.country),
    email: optional(values.email),
    invoice_email: optional(values.invoice_email),
    phone: optional(values.phone),
    dispatch_phone: optional(values.dispatch_phone),
    is_active: values.is_active,
    notes: optional(values.notes),
  };
}

export function CustomerFormDialog({
  open,
  customer,
  onClose,
  onSubmit,
  isSubmitting = false,
}: CustomerFormDialogProps) {
  const isEdit = Boolean(customer);
  const form = useForm<CustomerFormValues>({
    resolver: zodResolver(customerSchema),
    defaultValues: toFormValues(customer),
  });

  useEffect(() => {
    if (open) {
      form.reset(toFormValues(customer));
    }
  }, [open, customer, form]);

  const handleSubmit = form.handleSubmit(async (values) => {
    await onSubmit(toPayload(values));
  });

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>{isEdit ? "Edit customer" : "Add customer"}</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ pt: 1 }}>
          <Stack spacing={2}>
            <Typography variant="subtitle1" fontWeight={600}>
              Identity
            </Typography>
            <TextField
              label="Company name"
              fullWidth
              required
              error={Boolean(form.formState.errors.company_name)}
              helperText={form.formState.errors.company_name?.message}
              {...form.register("company_name")}
            />
            <TextField label="VAT number" fullWidth {...form.register("vat_number")} />
            <FormControlLabel
              control={
                <Switch
                  checked={form.watch("is_active")}
                  onChange={(e) => form.setValue("is_active", e.target.checked)}
                />
              }
              label="Active customer"
            />
            <TextField label="Notes" multiline minRows={2} fullWidth {...form.register("notes")} />
          </Stack>

          <Stack spacing={2}>
            <Typography variant="subtitle1" fontWeight={600}>
              Address
            </Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="Street" fullWidth {...form.register("street")} />
              <TextField label="House number" fullWidth {...form.register("house_number")} />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="Postal code" fullWidth {...form.register("postal_code")} />
              <TextField label="City" fullWidth {...form.register("city")} />
              <TextField label="Country" fullWidth {...form.register("country")} />
            </Stack>
            <TextField label="Full address (optional)" fullWidth {...form.register("address")} />
          </Stack>

          <Stack spacing={2}>
            <Typography variant="subtitle1" fontWeight={600}>
              Contacts
            </Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="General email" fullWidth {...form.register("email")} />
              <TextField label="Invoice email" fullWidth {...form.register("invoice_email")} />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="Phone" fullWidth {...form.register("phone")} />
              <TextField label="Dispatch phone" fullWidth {...form.register("dispatch_phone")} />
            </Stack>
          </Stack>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : isEdit ? "Save changes" : "Create customer"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
