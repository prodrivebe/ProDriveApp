import { Box, Typography } from "@mui/material";

interface StatTileProps {
  label: string;
  value: number | string;
  hint?: string;
  accent?: boolean;
}

export function StatTile({ label, value, hint, accent = false }: StatTileProps) {
  return (
    <Box
      sx={{
        p: 2.5,
        height: "100%",
        borderRadius: 3,
        border: 1,
        borderColor: "divider",
        bgcolor: "background.paper",
        boxShadow: 2,
        position: "relative",
        overflow: "hidden",
        transition: "box-shadow 200ms ease, transform 200ms ease",
        "&:hover": { boxShadow: 3, transform: "translateY(-1px)" },
        "&::before": accent
          ? {
              content: '""',
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              height: 3,
              bgcolor: "accent.main",
            }
          : undefined,
      }}
    >
      <Typography variant="overline" display="block" sx={{ mb: 0.5 }}>
        {label}
      </Typography>
      <Typography
        variant="h3"
        component="p"
        sx={{
          fontVariantNumeric: "tabular-nums",
          letterSpacing: "-0.02em",
          color: "primary.dark",
        }}
      >
        {value}
      </Typography>
      {hint ? (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
          {hint}
        </Typography>
      ) : null}
    </Box>
  );
}
