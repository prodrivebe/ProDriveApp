import { Link as RouterLink, useSearchParams } from "react-router-dom";
import AddIcon from "@mui/icons-material/Add";
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
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
import { ordersService } from "../services/ordersService";
import { customersService } from "../services/customersService";
import { driversService } from "../services/driversService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { StatusChip } from "../components/StatusChip";
import { PageHeader } from "../design-system";
import { formatDate, formatStopCities } from "../utils/format";
import { formatDriverName } from "../utils/driverDisplay";
import type { OrderDetail } from "../types/api";

const STATUS_OPTIONS = [
  "ALL",
  "DRAFT",
  "READY",
  "ASSIGNED",
  "IN_TRANSIT",
  "LOADING",
  "COMPLETED",
  "CANCELLED",
];

export function OrdersPage() {
  const [searchParams] = useSearchParams();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [status, setStatus] = useState("ALL");
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const ordersQuery = useQuery({
    queryKey: ["orders", page, pageSize, status, search],
    queryFn: () =>
      ordersService.list({
        page: page + 1,
        page_size: pageSize,
        status: status === "ALL" ? undefined : status,
        search: search || undefined,
      }),
  });

  const customersQuery = useQuery({
    queryKey: ["customers", "lookup"],
    queryFn: () => customersService.list({ page: 1, page_size: 100 }),
  });

  const driversQuery = useQuery({
    queryKey: ["drivers", "lookup"],
    queryFn: () => driversService.list({ page: 1, page_size: 100 }),
  });

  const customerMap = useMemo(() => {
    const map = new Map<string, string>();
    customersQuery.data?.items.forEach((c) => map.set(c.id, c.company_name));
    return map;
  }, [customersQuery.data]);

  const detailCache = useQuery({
    queryKey: ["orders", "details-for-list"],
    queryFn: async () => {
      const items = ordersQuery.data?.items ?? [];
      const details = await Promise.all(items.slice(0, 25).map((o) => ordersService.get(o.id)));
      return new Map(details.map((d) => [d.id, d]));
    },
    enabled: Boolean(ordersQuery.data?.items.length),
  });

  const filteredItems = useMemo(() => {
    let items = ordersQuery.data?.items ?? [];
    if (dateFrom) {
      items = items.filter((o) => o.planned_pickup_date && o.planned_pickup_date >= dateFrom);
    }
    if (dateTo) {
      items = items.filter((o) => o.planned_delivery_date && o.planned_delivery_date <= dateTo);
    }
    return items;
  }, [ordersQuery.data, dateFrom, dateTo]);

  if (ordersQuery.isLoading) return <LoadingState label="Loading orders..." />;
  if (ordersQuery.isError) return <ErrorAlert error={ordersQuery.error} />;

  const getDetail = (orderId: string): OrderDetail | undefined => detailCache.data?.get(orderId);

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Orders"
        subtitle="Manage transport orders and assignments"
        actions={
          <Button component={RouterLink} to="/orders/new" variant="contained" startIcon={<AddIcon />}>
            Create order
          </Button>
        }
      />

      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <TextField
          label="Search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          fullWidth
        />
        <FormControl sx={{ minWidth: 180 }}>
          <InputLabel>Status</InputLabel>
          <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
            {STATUS_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option.replaceAll("_", " ")}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          label="Pickup from"
          type="date"
          InputLabelProps={{ shrink: true }}
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
        />
        <TextField
          label="Delivery to"
          type="date"
          InputLabelProps={{ shrink: true }}
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
        />
      </Stack>

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Order #</TableCell>
            <TableCell>Customer</TableCell>
            <TableCell>Pickup</TableCell>
            <TableCell>Delivery</TableCell>
            <TableCell>Driver</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Vehicles</TableCell>
            <TableCell>Planned pickup</TableCell>
            <TableCell>Planned delivery</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {filteredItems.map((order) => {
            const detail = getDetail(order.id);
            return (
              <TableRow key={order.id} hover>
                <TableCell>
                  <Button component={RouterLink} to={`/orders/${order.id}`} size="small">
                    {order.order_number}
                  </Button>
                </TableCell>
                <TableCell>
                  {order.customer_name ?? customerMap.get(order.customer_id) ?? "—"}
                </TableCell>
                <TableCell>
                  {detail ? formatStopCities(detail.stops, "PICKUP") : "—"}
                </TableCell>
                <TableCell>
                  {detail ? formatStopCities(detail.stops, "DELIVERY") : "—"}
                </TableCell>
                <TableCell>
                  {order.assigned_driver_name ??
                    (order.assigned_driver_id
                      ? formatDriverName(
                          driversQuery.data?.items.find((d) => d.id === order.assigned_driver_id) ?? {
                            id: order.assigned_driver_id,
                            first_name: null,
                            last_name: null,
                            phone: null,
                          },
                        )
                      : "—")}
                </TableCell>
                <TableCell>
                  <StatusChip status={order.status} />
                </TableCell>
                <TableCell>{detail?.vehicles.length ?? "—"}</TableCell>
                <TableCell>{formatDate(order.planned_pickup_date)}</TableCell>
                <TableCell>{formatDate(order.planned_delivery_date)}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      <TablePagination
        component="div"
        count={ordersQuery.data?.total ?? 0}
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
