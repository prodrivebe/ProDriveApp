import {
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notificationsService } from "../services/notificationsService";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingState } from "../components/LoadingState";
import { formatDateTime } from "../utils/format";

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const notificationsQuery = useQuery({
    queryKey: ["notifications", "all"],
    queryFn: () => notificationsService.list(false),
  });

  const markAllMutation = useMutation({
    mutationFn: notificationsService.markAllRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markReadMutation = useMutation({
    mutationFn: notificationsService.markRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  if (notificationsQuery.isLoading) return <LoadingState />;
  if (notificationsQuery.isError) return <ErrorAlert error={notificationsQuery.error} />;

  return (
    <Stack spacing={3}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h4" fontWeight={700}>
          Notifications
        </Typography>
        <Button onClick={() => markAllMutation.mutate()} disabled={markAllMutation.isPending}>
          Mark all read
        </Button>
      </Stack>

      {(notificationsQuery.data ?? []).map((item) => (
        <Card key={item.id} variant={item.read_at ? "outlined" : "elevation"}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="start" gap={2}>
              <BoxContent item={item} />
              {!item.read_at ? (
                <Button size="small" onClick={() => markReadMutation.mutate(item.id)}>
                  Mark read
                </Button>
              ) : null}
            </Stack>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
}

function BoxContent({
  item,
}: {
  item: { title: string; message: string; type: string; created_at: string };
}) {
  return (
    <div>
      <Typography fontWeight={700}>{item.title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {item.message}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {item.type.replaceAll("_", " ")} · {formatDateTime(item.created_at)}
      </Typography>
    </div>
  );
}
