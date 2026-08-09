import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import type { PlanningBoardResponse, ResourceAvailability } from "../types/api";

function ResourceList({ title, items }: { title: string; items: ResourceAvailability[] }) {
  return (
    <Box>
      <Typography variant="subtitle2" fontWeight={700} gutterBottom>
        {title}
      </Typography>
      <List dense>
        {items.map((item) => (
          <ListItem key={item.id} disablePadding sx={{ mb: 0.5 }}>
            <ListItemText
              primary={item.label}
              secondary={item.capacity_indicator ?? `${item.active_assignments} active`}
            />
            <Chip
              size="small"
              label={item.available ? "Available" : "Busy"}
              color={item.conflict ? "error" : item.available ? "success" : "warning"}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}

export function AssignmentBoard({ board }: { board: PlanningBoardResponse }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6">Assignment board</Typography>
          <ResourceList title="Drivers" items={board.drivers} />
          <ResourceList title="Trucks" items={board.trucks} />
          <ResourceList title="Trailers" items={board.trailers} />
          {board.active_assignments.length ? (
            <Alert severity="info">{board.active_assignments.length} standing fleet assignments active</Alert>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}
