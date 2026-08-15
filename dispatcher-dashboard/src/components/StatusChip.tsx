import { Alert, Chip } from "@mui/material";

const STATUS_COLORS: Record<string, "default" | "primary" | "secondary" | "success" | "warning" | "error" | "info"> = {
  DRAFT: "default",
  READY: "info",
  ASSIGNED: "warning",
  ACCEPTED: "info",
  LOADING: "warning",
  IN_TRANSIT: "primary",
  DELIVERING: "primary",
  COMPLETED: "success",
  CANCELLED: "error",
};

export function StatusChip({ status }: { status: string }) {
  return <Chip label={status.replaceAll("_", " ")} color={STATUS_COLORS[status] ?? "default"} size="small" />;
}

export function ErrorAlert({ message }: { message: string | null }) {
  if (!message) {
    return null;
  }
  return (
    <Alert severity="error" sx={{ mb: 2 }}>
      {message}
    </Alert>
  );
}
