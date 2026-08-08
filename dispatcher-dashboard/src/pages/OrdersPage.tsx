import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { StatusChip } from "../components/StatusChip";
import { apiGetList } from "../services/apiClient";
import type { OrderListItem } from "../types/api";

export function OrdersPage() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState<OrderListItem[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const query = statusFilter
          ? `/orders?page=1&page_size=50&status=${statusFilter}`
          : "/orders?page=1&page_size=50";
        const result = await apiGetList<OrderListItem>(query);
        setOrders(result.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load orders.");
      }
    };
    void load();
  }, [statusFilter]);

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h4" fontWeight={700}>
          Orders
        </Typography>
        <Button component={RouterLink} to="/orders/new" variant="contained">
          Create order
        </Button>
      </Box>

      <TextField
        select
        label="Status filter"
        value={statusFilter}
        onChange={(e) => setStatusFilter(e.target.value)}
        SelectProps={{ native: true }}
        sx={{ maxWidth: 240 }}
      >
        <option value="">All statuses</option>
        {[
          "DRAFT",
          "READY",
          "ASSIGNED",
          "ACCEPTED",
          "LOADING",
          "IN_TRANSIT",
          "DELIVERING",
          "COMPLETED",
          "CANCELLED",
        ].map((status) => (
          <option key={status} value={status}>
            {status}
          </option>
        ))}
      </TextField>

      {error ? <Alert severity="error">{error}</Alert> : null}

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Order</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Pickup</TableCell>
              <TableCell>Delivery</TableCell>
              <TableCell>Vehicles</TableCell>
              <TableCell>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {orders.map((order) => (
              <TableRow
                key={order.id}
                hover
                onClick={() => navigate(`/orders/${order.id}`)}
                sx={{ cursor: "pointer" }}
              >
                <TableCell>{order.order_number}</TableCell>
                <TableCell>
                  <StatusChip status={order.status} />
                </TableCell>
                <TableCell>{order.planned_pickup_date ?? "—"}</TableCell>
                <TableCell>{order.planned_delivery_date ?? "—"}</TableCell>
                <TableCell>—</TableCell>
                <TableCell>{new Date(order.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
