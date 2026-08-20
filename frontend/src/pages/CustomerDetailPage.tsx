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
  TableRow,
  Typography,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { customersService } from "../services/customersService";
import { ordersService } from "../services/ordersService";
import { CustomerFormDialog } from "../components/CustomerFormDialog";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { StatusChip } from "../components/StatusChip";
import type { CustomerCreatePayload } from "../types/api";

export function CustomerDetailPage() {
  const { customerId = "" } = useParams();
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);

  const customerQuery = useQuery({
    queryKey: ["customers", customerId],
    queryFn: () => customersService.get(customerId),
    enabled: Boolean(customerId),
  });

  const contactsQuery = useQuery({
    queryKey: ["customers", customerId, "contacts"],
    queryFn: () => customersService.contacts(customerId),
    enabled: Boolean(customerId),
  });

  const ordersQuery = useQuery({
    queryKey: ["orders", "customer", customerId],
    queryFn: () => ordersService.list({ page: 1, page_size: 50, customer_id: customerId }),
    enabled: Boolean(customerId),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: CustomerCreatePayload) =>
      customersService.update(customerId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers", customerId] });
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      setEditOpen(false);
    },
  });

  if (customerQuery.isLoading) return <LoadingState />;
  if (customerQuery.isError) return <ErrorAlert error={customerQuery.error} />;

  const customer = customerQuery.data!;

  return (
    <Stack spacing={3}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h4" fontWeight={700}>
          {customer.company_name}
        </Typography>
        <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setEditOpen(true)}>
          Edit customer
        </Button>
      </Box>

      {updateMutation.isError ? <ErrorAlert error={updateMutation.error} /> : null}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Profile
          </Typography>
          <Typography>Status: {customer.is_active === false ? "Inactive" : "Active"}</Typography>
          <Typography>VAT: {customer.vat_number ?? "—"}</Typography>
          <Typography>
            Address:{" "}
            {[customer.street, customer.house_number, customer.postal_code, customer.city, customer.country]
              .filter(Boolean)
              .join(", ") || customer.address || "—"}
          </Typography>
          <Typography>Email: {customer.email ?? "—"}</Typography>
          <Typography>Invoice email: {customer.invoice_email ?? "—"}</Typography>
          <Typography>Phone: {customer.phone ?? "—"}</Typography>
          <Typography>Dispatch phone: {customer.dispatch_phone ?? "—"}</Typography>
          <Typography>Notes: {customer.notes ?? "—"}</Typography>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Contacts
          </Typography>
          {(contactsQuery.data ?? []).length === 0 ? (
            <Typography color="text.secondary">No contacts recorded.</Typography>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Phone</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(contactsQuery.data ?? []).map((contact) => (
                  <TableRow key={contact.id}>
                    <TableCell>{`${contact.first_name} ${contact.last_name}`}</TableCell>
                    <TableCell>{contact.email ?? "—"}</TableCell>
                    <TableCell>{contact.phone ?? "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Order history
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Order</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(ordersQuery.data?.items ?? []).map((order) => (
                <TableRow key={order.id}>
                  <TableCell>
                    <RouterLink to={`/orders/${order.id}`}>{order.order_number}</RouterLink>
                  </TableCell>
                  <TableCell>
                    <StatusChip status={order.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <CustomerFormDialog
        open={editOpen}
        customer={customer}
        onClose={() => setEditOpen(false)}
        onSubmit={(payload) => updateMutation.mutateAsync(payload)}
        isSubmitting={updateMutation.isPending}
      />
    </Stack>
  );
}
