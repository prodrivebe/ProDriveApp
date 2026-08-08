import { useEffect, useState } from "react";
import {
  Alert,
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
import { apiGet, apiGetList } from "../services/apiClient";
import type { Driver, FleetOverview, Trailer, Truck } from "../types/api";

export function FleetPage() {
  const [overview, setOverview] = useState<FleetOverview | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [trailers, setTrailers] = useState<Trailer[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [fleetOverview, driverList, truckList, trailerList] = await Promise.all([
          apiGet<FleetOverview>("/fleet/overview"),
          apiGetList<Driver>("/drivers?page=1&page_size=100"),
          apiGetList<Truck>("/trucks?page=1&page_size=100"),
          apiGetList<Trailer>("/trailers?page=1&page_size=100"),
        ]);
        setOverview(fleetOverview);
        setDrivers(driverList.items);
        setTrucks(truckList.items);
        setTrailers(trailerList.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load fleet.");
      }
    };
    void load();
  }, []);

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Fleet
      </Typography>

      {overview ? (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6">Drivers</Typography>
                <Typography>
                  {overview.drivers.active}/{overview.drivers.total} active
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6">Trucks</Typography>
                <Typography>
                  {overview.trucks.active}/{overview.trucks.total} active
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6">Trailers</Typography>
                <Typography>
                  {overview.trailers.active}/{overview.trailers.total} active
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : null}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Trucks
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Registration</TableCell>
                <TableCell>Active</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {trucks.map((truck) => (
                <TableRow key={truck.id}>
                  <TableCell>{truck.registration_number}</TableCell>
                  <TableCell>{truck.active ? "Yes" : "No"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Trailers
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Registration</TableCell>
                <TableCell>Active</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {trailers.map((trailer) => (
                <TableRow key={trailer.id}>
                  <TableCell>{trailer.registration_number}</TableCell>
                  <TableCell>{trailer.active ? "Yes" : "No"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Drivers
          </Typography>
          <Typography color="text.secondary">
            {drivers.length} driver profiles configured.
          </Typography>
        </CardContent>
      </Card>
    </Stack>
  );
}
