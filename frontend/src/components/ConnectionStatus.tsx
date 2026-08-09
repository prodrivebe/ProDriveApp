import { Chip } from "@mui/material";
import { useRealtime } from "../hooks/useRealtime";

const labels: Record<string, string> = {
  connected: "Live",
  connecting: "Connecting…",
  disconnected: "Offline",
  error: "Reconnecting…",
};

const colors: Record<string, "success" | "warning" | "default" | "error"> = {
  connected: "success",
  connecting: "warning",
  disconnected: "default",
  error: "error",
};

export function ConnectionStatus() {
  const { connectionState } = useRealtime();
  return (
    <Chip
      size="small"
      label={labels[connectionState] ?? connectionState}
      color={colors[connectionState] ?? "default"}
      variant={connectionState === "connected" ? "filled" : "outlined"}
    />
  );
}
