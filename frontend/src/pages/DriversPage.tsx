import { Link as RouterLink } from "react-router-dom";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import {
  Box,
  Button,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { driversService } from "../services/driversService";
import { ordersService } from "../services/ordersService";
import { DriverFormDialog } from "../components/DriverFormDialog";
import { formatDriverName } from "../utils/driverDisplay";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import type { Driver, DriverCreatePayload, DriverUpdatePayload } from "../types/api";

export function DriversPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingDriver, setEditingDriver] = useState<Driver | null>(null);

  const driversQuery = useQuery({
    queryKey: ["drivers", page, pageSize, search],
    queryFn: () =>
      driversService.list({
        page: page + 1,
        page_size: pageSize,
        search: search || undefined,
      }),
  });

  const ordersQuery = useQuery({
    queryKey: ["orders", "driver-assignments"],
    queryFn: () => ordersService.list({ page: 1, page_size: 100 }),
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: DriverCreatePayload | DriverUpdatePayload) => {
      if (editingDriver) {
        return driversService.update(editingDriver.id, payload as DriverUpdatePayload);
      }
      return driversService.create(payload as DriverCreatePayload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drivers"] });
      setDialogOpen(false);
      setEditingDriver(null);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (driver: Driver) => driversService.update(driver.id, { active: false }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["drivers"] }),
  });

  if (driversQuery.isLoading) return <LoadingState label="Loading drivers..." />;
  if (driversQuery.isError) return <ErrorAlert error={driversQuery.error} />;

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h4" fontWeight={700}>
          Drivers
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingDriver(null);
            setDialogOpen(true);
          }}
        >
          Add driver
        </Button>
      </Box>

      <TextField
        label="Search drivers"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        sx={{ maxWidth: 360 }}
      />

      {saveMutation.isError ? <ErrorAlert error={saveMutation.error} /> : null}
      {deactivateMutation.isError ? <ErrorAlert error={deactivateMutation.error} /> : null}

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Phone</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Current order</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {driversQuery.data.items.map((driver) => {
            const activeOrder = ordersQuery.data?.items.find(
              (order) =>
                order.assigned_driver_id === driver.id &&
                !["COMPLETED", "CANCELLED"].includes(order.status),
            );
            return (
              <TableRow key={driver.id} hover>
                <TableCell>
                  <RouterLink to={`/drivers/${driver.id}`}>{formatDriverName(driver)}</RouterLink>
                </TableCell>
                <TableCell>{driver.phone ?? "—"}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={driver.active ? "Available" : "Offline"}
                    color={driver.active ? "success" : "default"}
                  />
                </TableCell>
                <TableCell>
                  {activeOrder ? (
                    <RouterLink to={`/orders/${activeOrder.id}`}>{activeOrder.order_number}</RouterLink>
                  ) : (
                    "—"
                  )}
                </TableCell>
                <TableCell align="right">
                  <Button
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={() => {
                      setEditingDriver(driver);
                      setDialogOpen(true);
                    }}
                  >
                    Edit
                  </Button>
                  {driver.active ? (
                    <Button
                      size="small"
                      color="warning"
                      onClick={() => deactivateMutation.mutate(driver)}
                      disabled={deactivateMutation.isPending}
                    >
                      Deactivate
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      <TablePagination
        component="div"
        count={driversQuery.data.total}
        page={page}
        onPageChange={(_, next) => setPage(next)}
        rowsPerPage={pageSize}
        onRowsPerPageChange={(e) => {
          setPageSize(Number(e.target.value));
          setPage(0);
        }}
      />

      <DriverFormDialog
        open={dialogOpen}
        driver={editingDriver}
        onClose={() => {
          setDialogOpen(false);
          setEditingDriver(null);
        }}
        onSubmit={(payload) => saveMutation.mutateAsync(payload)}
        isSubmitting={saveMutation.isPending}
      />
    </Stack>
  );
}
