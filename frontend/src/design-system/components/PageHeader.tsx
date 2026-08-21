import { Box, Typography, type SxProps, type Theme } from "@mui/material";
import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  sx?: SxProps<Theme>;
}

export function PageHeader({ title, subtitle, actions, sx }: PageHeaderProps) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: { xs: "flex-start", sm: "center" },
        justifyContent: "space-between",
        gap: 2,
        mb: 3,
        flexWrap: "wrap",
        ...sx,
      }}
    >
      <Box>
        <Typography variant="h4" component="h1" sx={{ mb: subtitle ? 0.5 : 0 }}>
          {title}
        </Typography>
        {subtitle ? (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        ) : null}
      </Box>
      {actions ? <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>{actions}</Box> : null}
    </Box>
  );
}
