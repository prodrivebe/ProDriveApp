import { Box, CircularProgress, Typography } from "@mui/material";

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2, py: 4 }}>
      <CircularProgress size={24} />
      <Typography color="text.secondary">{label}</Typography>
    </Box>
  );
}
