import { Chip } from "@mui/material";

interface ConfidenceChipProps {
  label: string;
  confidence: number | undefined;
}

function confidenceColor(confidence: number | undefined): "success" | "warning" | "error" | "default" {
  if (confidence === undefined) return "default";
  if (confidence >= 0.85) return "success";
  if (confidence >= 0.7) return "warning";
  return "error";
}

export function ConfidenceChip({ label, confidence }: ConfidenceChipProps) {
  const pct = confidence !== undefined ? `${Math.round(confidence * 100)}%` : "—";
  return (
    <Chip
      size="small"
      label={`${label}: ${pct}`}
      color={confidenceColor(confidence)}
      variant="outlined"
    />
  );
}
