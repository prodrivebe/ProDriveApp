import { Button, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

export function DashboardPage() {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">Dashboard</Typography>
      <Typography color="text.secondary">Today's transport overview</Typography>
      <Button component={RouterLink} to="/orders/new" variant="contained">
        Create order
      </Button>
    </Stack>
  );
}

export function PlaceholderPage({ title }: { title: string }) {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">{title}</Typography>
      <Typography color="text.secondary">Module available in this build shell.</Typography>
    </Stack>
  );
}
