import { useEffect, useState } from "react";
import {
  Alert,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { apiGetList } from "../services/apiClient";
import type { Customer } from "../types/api";

export function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const result = await apiGetList<Customer>("/customers?page=1&page_size=100");
        setCustomers(result.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load customers.");
      }
    };
    void load();
  }, []);

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Customers
      </Typography>
      {error ? <Alert severity="error">{error}</Alert> : null}
      <Paper>
        <Table>
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
            {customers.map((customer) => (
              <TableRow key={customer.id}>
                <TableCell>{customer.company_name}</TableCell>
                <TableCell>{customer.city ?? "—"}</TableCell>
                <TableCell>{customer.country ?? "—"}</TableCell>
                <TableCell>{customer.email ?? "—"}</TableCell>
                <TableCell>{customer.phone ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
