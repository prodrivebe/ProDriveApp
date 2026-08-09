import { Alert, Box, Card, CardContent, Skeleton, Stack, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";

function StatCardSkeleton() {
  return (
    <Box sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 2, height: "100%" }}>
      <Skeleton variant="text" width="60%" />
      <Skeleton variant="text" width="40%" height={40} />
    </Box>
  );
}

export function DashboardSkeleton() {
  return (
    <Stack spacing={3}>
      <Box>
        <Skeleton variant="text" width={280} height={40} />
        <Skeleton variant="text" width={360} />
      </Box>
      <Grid container spacing={2}>
        {Array.from({ length: 8 }).map((_, index) => (
          <Grid key={index} size={{ xs: 12, sm: 6, md: 3 }}>
            <StatCardSkeleton />
          </Grid>
        ))}
      </Grid>
      <Card variant="outlined">
        <CardContent>
          <Skeleton variant="text" width="30%" />
          <Skeleton variant="rectangular" height={240} sx={{ mt: 2, borderRadius: 1 }} />
        </CardContent>
      </Card>
    </Stack>
  );
}

export function DashboardEmptyState() {
  return (
    <Alert severity="info">
      No transport activity yet. Create your first order to populate the operations board.
    </Alert>
  );
}
