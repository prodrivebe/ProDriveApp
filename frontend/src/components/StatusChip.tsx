import { Chip } from "@mui/material";
import { orderStatusVariant, StatusBadge } from "../design-system";

export function StatusChip({ status }: { status: string }) {
  const label = status.replaceAll("_", " ");
  const variant = orderStatusVariant(status);
  return <StatusBadge label={label} variant={variant} />;
}

/** @deprecated Use StatusBadge directly for non-order statuses */
export { StatusBadge, orderStatusVariant };
