import { Link as RouterLink } from "react-router-dom";
import {
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
import { useState } from "react";
import { customersService } from "../services/customersService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";

export function CustomersPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [search, setSearch] = useState("");

  const customersQuery = useQuery({
    queryKey: ["customers", page, pageSize, search],
    queryFn: () =>
      customersService.list({
        page: page + 1,
        page_size: pageSize,
        search: search || undefined,
      }),
  });

  if (customersQuery.isLoading) return <LoadingState label="Loading customers..." />;
  if (customersQuery.isError) return <ErrorAlert error={customersQuery.error} />;

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Customers
      </Typography>
      <TextField
        label="Search customers"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        sx={{ maxWidth: 360 }}
      />
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Company</TableCell>
            <TableCell>City</TableCell>
            <TableCell>Country</TableCell>
            <TableCell>Email</TableCell>
            <TableCell>Phone</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {customersQuery.data.items.map((customer) => (
            <TableRow key={customer.id} hover>
              <TableCell>
                <RouterLink to={`/customers/${customer.id}`}>{customer.company_name}</RouterLink>
              </TableCell>
              <TableCell>{customer.city ?? "—"}</TableCell>
              <TableCell>{customer.country ?? "—"}</TableCell>
              <TableCell>{customer.email ?? "—"}</TableCell>
              <TableCell>{customer.phone ?? "—"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <TablePagination
        component="div"
        count={customersQuery.data.total}
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
