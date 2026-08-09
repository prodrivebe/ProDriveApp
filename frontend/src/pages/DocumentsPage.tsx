import { Link as RouterLink } from "react-router-dom";
import {
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { ordersService } from "../services/ordersService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { formatDateTime } from "../utils/format";
import { resolveUploadUrl } from "../app/config";
import type { OrderDocument } from "../types/api";

export function DocumentsPage() {
  const ordersQuery = useQuery({
    queryKey: ["orders", "documents-index"],
    queryFn: () => ordersService.list({ page: 1, page_size: 50 }),
  });

  const documentsQuery = useQuery({
    queryKey: ["documents", "all", ordersQuery.data?.items.map((o) => o.id)],
    queryFn: async () => {
      const orders = ordersQuery.data?.items ?? [];
      const nested = await Promise.all(
        orders.map(async (order) => {
          const docs = await ordersService.listDocuments(order.id);
          return docs.map((doc) => ({ ...doc, order_number: order.order_number }));
        }),
      );
      return nested.flat() as Array<OrderDocument & { order_number: string }>;
    },
    enabled: Boolean(ordersQuery.data?.items.length),
  });

  if (ordersQuery.isLoading || documentsQuery.isLoading) {
    return <LoadingState label="Loading documents..." />;
  }
  if (ordersQuery.isError) return <ErrorAlert error={ordersQuery.error} />;
  if (documentsQuery.isError) return <ErrorAlert error={documentsQuery.error} />;

  const documents = [...(documentsQuery.data ?? [])].sort(
    (a, b) => new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime(),
  );

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Documents
      </Typography>
      <Typography color="text.secondary">
        Recent order documents across active orders. Upload CMR and other files from the order detail page.
      </Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Order</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>File</TableCell>
            <TableCell>Version</TableCell>
            <TableCell>Uploaded</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {documents.map((doc) => (
            <TableRow key={doc.id}>
              <TableCell>
                <RouterLink to={`/orders/${doc.order_id}`}>{doc.order_number}</RouterLink>
              </TableCell>
              <TableCell>{doc.document_type}</TableCell>
              <TableCell>{doc.file_name}</TableCell>
              <TableCell>v{doc.version}</TableCell>
              <TableCell>{formatDateTime(doc.uploaded_at)}</TableCell>
              <TableCell>
                <a href={resolveUploadUrl(doc.file_path)} target="_blank" rel="noreferrer">
                  Preview
                </a>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Stack>
  );
}
