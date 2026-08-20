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
import type { Driver, DriverCreatePayload, DriverUpdatePayload } from "../types/api";

const driverSchema = z.object({
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  password: z.string().optional(),
  phone: z.string().optional(),
  address: z.string().optional(),
  country: z.string().optional(),
  date_of_birth: z.string().optional(),
  id_document_number: z.string().optional(),
  id_expiry: z.string().optional(),
  driving_license: z.string().optional(),
  driving_licence_expiry: z.string().optional(),
  adr_certificate: z.string().optional(),
  code95_expiry: z.string().optional(),
  tachograph_card_number: z.string().optional(),
  tachograph_card_expiry: z.string().optional(),
  visa_residence_expiry: z.string().optional(),
  notes: z.string().optional(),
  active: z.boolean(),
});

type DriverFormValues = z.infer<typeof driverSchema>;

interface DriverFormDialogProps {
  open: boolean;
  driver?: Driver | null;
  onClose: () => void;
  onSubmit: (payload: DriverCreatePayload | DriverUpdatePayload) => Promise<void>;
  isSubmitting?: boolean;
}

function toFormValues(driver?: Driver | null): DriverFormValues {
  return {
    first_name: driver?.first_name ?? "",
    last_name: driver?.last_name ?? "",
    email: driver?.email ?? "",
    password: "",
    phone: driver?.phone ?? "",
    address: driver?.address ?? "",
    country: driver?.country ?? "",
    date_of_birth: driver?.date_of_birth ?? "",
    id_document_number: driver?.id_document_number ?? "",
    id_expiry: driver?.id_expiry ?? "",
    driving_license: driver?.driving_license ?? "",
    driving_licence_expiry: driver?.driving_licence_expiry ?? "",
    adr_certificate: driver?.adr_certificate ?? "",
    code95_expiry: driver?.code95_expiry ?? "",
    tachograph_card_number: driver?.tachograph_card_number ?? "",
    tachograph_card_expiry: driver?.tachograph_card_expiry ?? "",
    visa_residence_expiry: driver?.visa_residence_expiry ?? "",
    notes: driver?.notes ?? "",
    active: driver?.active ?? true,
  };
}

function optionalText(value: string | undefined): string | null {
  return value?.trim() || null;
}

function toPayload(values: DriverFormValues, isEdit: boolean): DriverCreatePayload | DriverUpdatePayload {
  const base = {
    phone: optionalText(values.phone),
    address: optionalText(values.address),
    country: optionalText(values.country),
    date_of_birth: optionalText(values.date_of_birth),
    id_document_number: optionalText(values.id_document_number),
    id_expiry: optionalText(values.id_expiry),
    driving_license: optionalText(values.driving_license),
    driving_licence_expiry: optionalText(values.driving_licence_expiry),
    adr_certificate: optionalText(values.adr_certificate),
    code95_expiry: optionalText(values.code95_expiry),
    tachograph_card_number: optionalText(values.tachograph_card_number),
    tachograph_card_expiry: optionalText(values.tachograph_card_expiry),
    visa_residence_expiry: optionalText(values.visa_residence_expiry),
    notes: optionalText(values.notes),
    active: values.active,
  };

  if (isEdit) {
    return {
      ...base,
      first_name: optionalText(values.first_name),
      last_name: optionalText(values.last_name),
      email: optionalText(values.email),
    };
  }

  return {
    ...base,
    first_name: values.first_name?.trim() || undefined,
    last_name: values.last_name?.trim() || undefined,
    email: values.email?.trim() || undefined,
    password: values.password?.trim() || undefined,
  };
}

export function DriverFormDialog({
  open,
  driver,
  onClose,
  onSubmit,
  isSubmitting = false,
}: DriverFormDialogProps) {
  const isEdit = Boolean(driver);
  const form = useForm<DriverFormValues>({
    resolver: zodResolver(driverSchema),
    defaultValues: toFormValues(driver),
  });

  useEffect(() => {
    if (open) {
      form.reset(toFormValues(driver));
    }
  }, [open, driver, form]);

  const handleSubmit = form.handleSubmit(async (values) => {
    await onSubmit(toPayload(values, isEdit));
  });

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>{isEdit ? "Edit driver" : "Add driver"}</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ pt: 1 }}>
          <Stack spacing={2}>
            <Typography variant="subtitle1" fontWeight={600}>
              Personal info
            </Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="First name" fullWidth {...form.register("first_name")} />
              <TextField label="Last name" fullWidth {...form.register("last_name")} />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="Email" fullWidth {...form.register("email")} />
              {!isEdit ? (
                <TextField
                  label="Password"
                  type="password"
                  fullWidth
                  helperText="Required for new driver login"
                  {...form.register("password")}
                />
              ) : null}
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="Phone" fullWidth {...form.register("phone")} />
              <TextField
                label="Date of birth"
                type="date"
                InputLabelProps={{ shrink: true }}
                fullWidth
                {...form.register("date_of_birth")}
              />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="Address" fullWidth {...form.register("address")} />
              <TextField label="Country" fullWidth {...form.register("country")} />
            </Stack>
            <FormControlLabel
              control={
                <Switch
                  checked={form.watch("active")}
                  onChange={(e) => form.setValue("active", e.target.checked)}
                />
              }
              label="Active driver"
            />
            <TextField label="Notes" multiline minRows={2} fullWidth {...form.register("notes")} />
          </Stack>

          <Stack spacing={2}>
            <Typography variant="subtitle1" fontWeight={600}>
              Documents &amp; expiry
            </Typography>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="ID document number" fullWidth {...form.register("id_document_number")} />
              <TextField
                label="ID expiry"
                type="date"
                InputLabelProps={{ shrink: true }}
                fullWidth
                {...form.register("id_expiry")}
              />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="Driving licence number" fullWidth {...form.register("driving_license")} />
              <TextField
                label="Driving licence expiry"
                type="date"
                InputLabelProps={{ shrink: true }}
                fullWidth
                {...form.register("driving_licence_expiry")}
              />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField label="ADR certificate" fullWidth {...form.register("adr_certificate")} />
              <TextField
                label="Code 95 expiry"
                type="date"
                InputLabelProps={{ shrink: true }}
                fullWidth
                {...form.register("code95_expiry")}
              />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                label="Tachograph card number"
                fullWidth
                {...form.register("tachograph_card_number")}
              />
              <TextField
                label="Tachograph card expiry"
                type="date"
                InputLabelProps={{ shrink: true }}
                fullWidth
                {...form.register("tachograph_card_expiry")}
              />
            </Stack>
            <TextField
              label="Visa / residence expiry"
              type="date"
              InputLabelProps={{ shrink: true }}
              fullWidth
              {...form.register("visa_residence_expiry")}
            />
          </Stack>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : isEdit ? "Save changes" : "Create driver"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
