import { Link as RouterLink } from "react-router-dom";
import {
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
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { driversService } from "../services/driversService";
import { ordersService } from "../services/ordersService";
import { apiGetList } from "../services/apiClient";
import type { UserProfile } from "../types/api";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";

export function DriversPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [search, setSearch] = useState("");

  const driversQuery = useQuery({
    queryKey: ["drivers", page, pageSize, search],
    queryFn: () =>
      driversService.list({
        page: page + 1,
        page_size: pageSize,
        search: search || undefined,
      }),
  });

  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: () => apiGetList<UserProfile>("/users", { page: 1, page_size: 200 }),
  });

  const ordersQuery = useQuery({
    queryKey: ["orders", "driver-assignments"],
    queryFn: () => ordersService.list({ page: 1, page_size: 200 }),
  });

  const userMap = useMemo(() => {
    const map = new Map<string, UserProfile>();
    usersQuery.data?.items.forEach((user) => map.set(user.id, user));
    return map;
  }, [usersQuery.data]);

  if (driversQuery.isLoading) return <LoadingState label="Loading drivers..." />;
  if (driversQuery.isError) return <ErrorAlert error={driversQuery.error} />;

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Drivers
      </Typography>
      <TextField
        label="Search drivers"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        sx={{ maxWidth: 360 }}
      />
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Phone</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Current order</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {driversQuery.data.items.map((driver) => {
            const user = userMap.get(driver.user_id);
            const activeOrder = ordersQuery.data?.items.find(
              (order) =>
                order.assigned_driver_id === driver.id &&
                !["COMPLETED", "CANCELLED"].includes(order.status),
            );
            return (
              <TableRow key={driver.id} hover>
                <TableCell>
                  <RouterLink to={`/drivers/${driver.id}`}>
                    {user ? `${user.first_name} ${user.last_name}` : driver.id.slice(0, 8)}
                  </RouterLink>
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
    </Stack>
  );
}
