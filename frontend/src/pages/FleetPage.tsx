import {
  Card,
  CardContent,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useQuery } from "@tanstack/react-query";
import { fleetService } from "../services/fleetService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";

export function FleetPage() {
  const overviewQuery = useQuery({
    queryKey: ["fleet", "overview"],
    queryFn: fleetService.overview,
  });
  const trucksQuery = useQuery({
    queryKey: ["trucks"],
    queryFn: () => fleetService.listTrucks({ page: 1, page_size: 100 }),
  });
  const trailersQuery = useQuery({
    queryKey: ["trailers"],
    queryFn: () => fleetService.listTrailers({ page: 1, page_size: 100 }),
  });

  if (overviewQuery.isLoading) return <LoadingState label="Loading fleet..." />;
  if (overviewQuery.isError) return <ErrorAlert error={overviewQuery.error} />;

  const overview = overviewQuery.data;

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Fleet
      </Typography>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Trucks</Typography>
              <Typography variant="h4">
                {overview.trucks.active}/{overview.trucks.total}
              </Typography>
              <Typography color="text.secondary">Active trucks</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Trailers</Typography>
              <Typography variant="h4">
                {overview.trailers.active}/{overview.trailers.total}
              </Typography>
              <Typography color="text.secondary">Active trailers</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">Drivers</Typography>
              <Typography variant="h4">
                {overview.drivers.active}/{overview.drivers.total}
              </Typography>
              <Typography color="text.secondary">Active drivers</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="h6" gutterBottom>
            Trucks
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Registration</TableCell>
                <TableCell>Make / Model</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(trucksQuery.data?.items ?? []).map((truck) => (
                <TableRow key={truck.id}>
                  <TableCell>{truck.registration_number}</TableCell>
                  <TableCell>{[truck.make, truck.model].filter(Boolean).join(" ") || "—"}</TableCell>
                  <TableCell>{truck.active ? "Active" : "Inactive"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="h6" gutterBottom>
            Trailers
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Registration</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(trailersQuery.data?.items ?? []).map((trailer) => (
                <TableRow key={trailer.id}>
                  <TableCell>{trailer.registration_number}</TableCell>
                  <TableCell>{trailer.trailer_type ?? "—"}</TableCell>
                  <TableCell>{trailer.active ? "Active" : "Inactive"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Grid>
      </Grid>
    </Stack>
  );
}
