import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import { apiGet, apiPost } from "../services/apiClient";
import type { Notification } from "../types/api";

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await apiGet<Notification[]>("/notifications");
      setNotifications(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load notifications.");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const markAllRead = async () => {
    await apiPost("/notifications/read-all");
    await load();
  };

  return (
    <Stack spacing={3}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h4" fontWeight={700}>
          Notifications
        </Typography>
        <Button variant="outlined" onClick={markAllRead}>
          Mark all read
        </Button>
      </Stack>
      {error ? <Alert severity="error">{error}</Alert> : null}
      <List>
        {notifications.map((item) => (
          <ListItem key={item.id} divider>
            <ListItemText
              primary={item.title}
              secondary={`${item.message} • ${new Date(item.created_at).toLocaleString()}`}
            />
          </ListItem>
        ))}
      </List>
    </Stack>
  );
}
