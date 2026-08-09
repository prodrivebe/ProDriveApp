import { Link as RouterLink, useParams } from "react-router-dom";
import {
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
import { useQuery } from "@tanstack/react-query";
import { customersService } from "../services/customersService";
import { ordersService } from "../services/ordersService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { StatusChip } from "../components/StatusChip";

export function CustomerDetailPage() {
  const { customerId = "" } = useParams();

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

  if (customerQuery.isLoading) return <LoadingState />;
  if (customerQuery.isError) return <ErrorAlert error={customerQuery.error} />;

  const customer = customerQuery.data!;

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        {customer.company_name}
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Profile
          </Typography>
          <Typography>City: {customer.city ?? "—"}</Typography>
          <Typography>Country: {customer.country ?? "—"}</Typography>
          <Typography>Email: {customer.email ?? "—"}</Typography>
          <Typography>Phone: {customer.phone ?? "—"}</Typography>
          <Typography>Address: {customer.address ?? "—"}</Typography>
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
    </Stack>
  );
}
