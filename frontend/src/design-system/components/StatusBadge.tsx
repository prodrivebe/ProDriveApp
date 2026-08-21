import { Chip, type ChipProps } from "@mui/material";

export type StatusBadgeVariant =
  | "default"
  | "active"
  | "available"
  | "busy"
  | "pending"
  | "inTransit"
  | "completed"
  | "cancelled"
  | "maintenance"
  | "expired"
  | "info"
  | "warning"
  | "success"
  | "error";

const VARIANT_STYLES: Record<
  StatusBadgeVariant,
  { bgcolor: string; color: string; border: string }
> = {
  default: { bgcolor: "action.hover", color: "text.secondary", border: "divider" },
  active: { bgcolor: "success.light", color: "success.main", border: "success.main" },
  available: { bgcolor: "success.light", color: "success.main", border: "success.main" },
  busy: { bgcolor: "warning.light", color: "warning.main", border: "warning.main" },
  pending: { bgcolor: "info.light", color: "info.main", border: "info.main" },
  inTransit: { bgcolor: "info.light", color: "info.main", border: "info.main" },
  completed: { bgcolor: "success.light", color: "success.main", border: "success.main" },
  cancelled: { bgcolor: "error.light", color: "error.main", border: "error.main" },
  maintenance: { bgcolor: "warning.light", color: "warning.main", border: "warning.main" },
  expired: { bgcolor: "error.light", color: "error.main", border: "error.main" },
  info: { bgcolor: "info.light", color: "info.main", border: "info.main" },
  warning: { bgcolor: "warning.light", color: "warning.main", border: "warning.main" },
  success: { bgcolor: "success.light", color: "success.main", border: "success.main" },
  error: { bgcolor: "error.light", color: "error.main", border: "error.main" },
};

interface StatusBadgeProps extends Omit<ChipProps, "color" | "variant"> {
  label: string;
  variant?: StatusBadgeVariant;
}

export function StatusBadge({ label, variant = "default", sx, ...props }: StatusBadgeProps) {
  const style = VARIANT_STYLES[variant];
  return (
    <Chip
      label={label}
      size="small"
      sx={{
        bgcolor: style.bgcolor,
        color: style.color,
        border: 1,
        borderColor: style.border,
        fontWeight: 600,
        ...sx,
      }}
      {...props}
    />
  );
}

const ORDER_STATUS_VARIANT: Record<string, StatusBadgeVariant> = {
  DRAFT: "default",
  READY: "pending",
  ASSIGNED: "info",
  ACCEPTED: "info",
  ARRIVED_PICKUP: "pending",
  LOADING: "warning",
  LOADED: "warning",
  IN_TRANSIT: "inTransit",
  ARRIVED_DELIVERY: "inTransit",
  DELIVERING: "busy",
  COMPLETED: "completed",
  CANCELLED: "cancelled",
};

export function orderStatusVariant(status: string): StatusBadgeVariant {
  return ORDER_STATUS_VARIANT[status] ?? "default";
}
