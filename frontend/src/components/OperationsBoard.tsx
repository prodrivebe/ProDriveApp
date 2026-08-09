import { Link as RouterLink } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useQuery } from "@tanstack/react-query";
import { ordersService } from "../services/ordersService";
import { presenceService } from "../services/presenceService";
import type { OrderSummary } from "../types/api";
import { isToday } from "../utils/format";

interface BoardColumn {
  id: string;
  title: string;
  filter: (order: OrderSummary) => boolean;
}

const columns: BoardColumn[] = [
  {
    id: "unassigned",
    title: "Unassigned",
    filter: (order) => ["READY", "DRAFT"].includes(order.status),
  },
  {
    id: "assigned",
    title: "Assigned",
    filter: (order) => order.status === "ASSIGNED",
  },
  {
    id: "accepted",
    title: "Accepted",
    filter: (order) => ["ACCEPTED", "ARRIVED_PICKUP"].includes(order.status),
  },
  {
    id: "loading",
    title: "Loading",
    filter: (order) => ["LOADING", "LOADED"].includes(order.status),
  },
  {
    id: "in_transit",
    title: "In Transit",
    filter: (order) => ["IN_TRANSIT", "ARRIVED_DELIVERY"].includes(order.status),
  },
  {
    id: "delivering",
    title: "Delivering",
    filter: (order) => order.status === "DELIVERING",
  },
  {
    id: "completed_today",
    title: "Completed Today",
    filter: (order) => order.status === "COMPLETED" && isToday(order.updated_at),
  },
  {
    id: "delayed",
    title: "Delayed",
    filter: (order) =>
      !["COMPLETED", "CANCELLED"].includes(order.status) &&
      Boolean(order.planned_delivery_date) &&
      new Date(order.planned_delivery_date!) < new Date(),
  },
];

function OrderCard({ order }: { order: OrderSummary }) {
  return (
    <Card variant="outlined" sx={{ mb: 1 }}>
      <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
        <Typography
          component={RouterLink}
          to={`/orders/${order.id}`}
          variant="subtitle2"
          sx={{ fontWeight: 700, textDecoration: "none", color: "inherit" }}
        >
          {order.order_number}
        </Typography>
        <Chip size="small" label={order.status.replaceAll("_", " ")} sx={{ mt: 1 }} />
      </CardContent>
    </Card>
  );
}

export function OperationsBoard() {
  const ordersQuery = useQuery({
    queryKey: ["orders", "board"],
    queryFn: () => ordersService.list({ page: 1, page_size: 200 }),
  });
  const presenceQuery = useQuery({
    queryKey: ["presence"],
    queryFn: () => presenceService.list(),
    refetchInterval: 60_000,
  });

  const orders = ordersQuery.data?.items ?? [];
  const onlineDrivers = (presenceQuery.data ?? []).filter((item) => item.role === "DRIVER");

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip label={`${onlineDrivers.length} drivers online`} color="success" variant="outlined" />
        {(presenceQuery.data ?? [])
          .filter((item) => item.role === "DISPATCHER" || item.role === "ADMIN")
          .slice(0, 5)
          .map((item) => (
            <Chip key={item.user_id} size="small" label={`${item.role}: ${item.status}`} />
          ))}
      </Stack>

      <Grid container spacing={2} sx={{ overflowX: "auto", flexWrap: "nowrap", pb: 1 }}>
        {columns.map((column) => {
          const items = orders.filter(column.filter);
          return (
            <Grid key={column.id} size={{ xs: 10, sm: 6, md: 3 }} sx={{ minWidth: 240 }}>
              <Box sx={{ bgcolor: "action.hover", borderRadius: 2, p: 1.5, minHeight: 320 }}>
                <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                  {column.title}
                </Typography>
                <Chip size="small" label={items.length} sx={{ mb: 1.5 }} />
                {items.map((order) => (
                  <OrderCard key={order.id} order={order} />
                ))}
              </Box>
            </Grid>
          );
        })}
      </Grid>
    </Stack>
  );
}
