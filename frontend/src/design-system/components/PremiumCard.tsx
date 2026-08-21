import { Box, Typography, type SxProps, type Theme } from "@mui/material";
import type { ReactNode } from "react";

interface PremiumCardProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
  elevated?: boolean;
  sx?: SxProps<Theme>;
  contentSx?: SxProps<Theme>;
}

export function PremiumCard({
  title,
  subtitle,
  children,
  actions,
  elevated = false,
  sx,
  contentSx,
}: PremiumCardProps) {
  return (
    <Box
      sx={{
        borderRadius: 3,
        border: 1,
        borderColor: "divider",
        bgcolor: elevated ? "surface.elevated" : "background.paper",
        boxShadow: elevated ? 3 : 2,
        overflow: "hidden",
        ...sx,
      }}
    >
      {title || actions ? (
        <Box
          sx={{
            px: 2.5,
            py: 2,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 2,
            borderBottom: 1,
            borderColor: "divider",
            bgcolor: "surface.elevated",
          }}
        >
          <Box>
            {title ? <Typography variant="h6">{title}</Typography> : null}
            {subtitle ? (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            ) : null}
          </Box>
          {actions}
        </Box>
      ) : null}
      <Box sx={{ p: 2.5, ...contentSx }}>{children}</Box>
    </Box>
  );
}
