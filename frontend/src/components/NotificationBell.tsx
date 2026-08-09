import { useNavigate } from "react-router-dom";
import NotificationsNoneIcon from "@mui/icons-material/NotificationsNone";
import { Badge, IconButton, Menu, MenuItem, Typography } from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { notificationsService } from "../services/notificationsService";

export function NotificationBell() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [anchor, setAnchor] = useState<null | HTMLElement>(null);

  const notificationsQuery = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => notificationsService.list(true),
  });

  const markReadMutation = useMutation({
    mutationFn: notificationsService.markRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const unread = notificationsQuery.data ?? [];
  const preview = unread.slice(0, 5);

  return (
    <>
      <IconButton aria-label="Notifications" onClick={(e) => setAnchor(e.currentTarget)}>
        <Badge badgeContent={unread.length} color="error">
          <NotificationsNoneIcon />
        </Badge>
      </IconButton>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)}>
        {preview.length === 0 ? (
          <MenuItem disabled>No unread notifications</MenuItem>
        ) : (
          preview.map((item) => (
            <MenuItem
              key={item.id}
              onClick={() => {
                markReadMutation.mutate(item.id);
                setAnchor(null);
                const orderId = (item as { order_id?: string | null }).order_id;
                if (orderId) {
                  navigate(`/orders/${orderId}`);
                }
              }}
            >
              <Typography variant="body2" fontWeight={600}>
                {item.title}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {item.message}
              </Typography>
            </MenuItem>
          ))
        )}
        <MenuItem
          onClick={() => {
            setAnchor(null);
            navigate("/notifications");
          }}
        >
          View all
        </MenuItem>
      </Menu>
    </>
  );
}
