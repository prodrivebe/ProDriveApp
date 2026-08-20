import { Link as RouterLink, useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
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
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { customersService } from "../services/customersService";
import { CustomerFormDialog } from "../components/CustomerFormDialog";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import type { Customer, CustomerCreatePayload } from "../types/api";

export function CustomersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);

  const customersQuery = useQuery({
    queryKey: ["customers", page, pageSize, search],
    queryFn: () =>
      customersService.list({
        page: page + 1,
        page_size: pageSize,
        search: search || undefined,
      }),
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: CustomerCreatePayload) => {
      if (editingCustomer) {
        return customersService.update(editingCustomer.id, payload);
      }
      return customersService.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      setDialogOpen(false);
      setEditingCustomer(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (customerId: string) => customersService.delete(customerId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["customers"] }),
  });

  if (customersQuery.isLoading) return <LoadingState label="Loading customers..." />;
  if (customersQuery.isError) return <ErrorAlert error={customersQuery.error} />;

  const openCreate = () => {
    setEditingCustomer(null);
    setDialogOpen(true);
  };

  const openEdit = (customer: Customer) => {
    setEditingCustomer(customer);
    setDialogOpen(true);
  };

  const handleDelete = (customer: Customer) => {
    if (window.confirm(`Delete customer "${customer.company_name}"?`)) {
      deleteMutation.mutate(customer.id);
    }
  };

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h4" fontWeight={700}>
          Customers
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          Add customer
        </Button>
      </Box>

      <TextField
        label="Search customers"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        sx={{ maxWidth: 360 }}
      />

      {deleteMutation.isError ? <ErrorAlert error={deleteMutation.error} /> : null}
      {saveMutation.isError ? <ErrorAlert error={saveMutation.error} /> : null}

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Company</TableCell>
            <TableCell>City</TableCell>
            <TableCell>Country</TableCell>
            <TableCell>Email</TableCell>
            <TableCell>Phone</TableCell>
            <TableCell>Status</TableCell>
            <TableCell align="right">Actions</TableCell>
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
              <TableCell>{customer.is_active === false ? "Inactive" : "Active"}</TableCell>
              <TableCell align="right">
                <Button size="small" startIcon={<EditIcon />} onClick={() => openEdit(customer)}>
                  Edit
                </Button>
                <Button
                  size="small"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => handleDelete(customer)}
                  disabled={deleteMutation.isPending}
                >
                  Delete
                </Button>
              </TableCell>
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

      <CustomerFormDialog
        open={dialogOpen}
        customer={editingCustomer}
        onClose={() => {
          setDialogOpen(false);
          setEditingCustomer(null);
        }}
        onSubmit={(payload) => saveMutation.mutateAsync(payload)}
        isSubmitting={saveMutation.isPending}
      />
    </Stack>
  );
}
