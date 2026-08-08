import { Chip, type ChipProps } from "@mui/material";

const STATUS_COLORS: Record<string, ChipProps["color"]> = {
  DRAFT: "default",
  READY: "info",
  ASSIGNED: "warning",
  ACCEPTED: "primary",
  LOADING: "secondary",
  IN_TRANSIT: "info",
  DELIVERING: "warning",
  COMPLETED: "success",
  CANCELLED: "error",
};

export function StatusChip({ status }: { status: string }) {
  return (
    <Chip
      label={status.replaceAll("_", " ")}
      color={STATUS_COLORS[status] ?? "default"}
      size="small"
    />
  );
}
