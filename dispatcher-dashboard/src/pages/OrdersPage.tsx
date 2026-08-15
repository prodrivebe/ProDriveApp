import {
  Button,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { apiGetPaginated } from "../api/client";
import { ErrorAlert, StatusChip } from "../components/StatusChip";
import type { OrderSummary } from "../types/domain";

const STATUS_OPTIONS = [
  "",
  "DRAFT",
  "READY",
  "ASSIGNED",
  "ACCEPTED",
  "LOADING",
  "IN_TRANSIT",
  "DELIVERING",
  "COMPLETED",
  "CANCELLED",
];

export function OrdersPage() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const path = statusFilter
          ? `/orders?page=1&page_size=50&status=${statusFilter}`
          : "/orders?page=1&page_size=50";
        const result = await apiGetPaginated<OrderSummary>(path);
        setOrders(result.items);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load orders.");
      }
    })();
  }, [statusFilter]);

  return (
    <Stack spacing={3}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">Orders</Typography>
        <Button component={RouterLink} to="/orders/new" variant="contained">
          Create order
        </Button>
      </Stack>
      <TextField
        select
        label="Status filter"
        value={statusFilter}
        onChange={(event) => setStatusFilter(event.target.value)}
        SelectProps={{ native: true }}
        sx={{ maxWidth: 240 }}
      >
        {STATUS_OPTIONS.map((status) => (
          <option key={status || "all"} value={status}>
            {status || "All statuses"}
          </option>
        ))}
      </TextField>
      <ErrorAlert message={error} />
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Order</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Pickup</TableCell>
              <TableCell>Delivery</TableCell>
              <TableCell>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {orders.map((order) => (
              <TableRow
                key={order.id}
                hover
                sx={{ cursor: "pointer" }}
                onClick={() => navigate(`/orders/${order.id}`)}
              >
                <TableCell>{order.order_number}</TableCell>
                <TableCell>
                  <StatusChip status={order.status} />
                </TableCell>
                <TableCell>{order.planned_pickup_date ?? "—"}</TableCell>
                <TableCell>{order.planned_delivery_date ?? "—"}</TableCell>
                <TableCell>{new Date(order.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}
