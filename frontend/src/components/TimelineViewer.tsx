import type { OrderTimelineEntry } from "../types/api";
import { formatDateTime } from "../utils/format";
import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";

export function TimelineViewer({ entries }: { entries: OrderTimelineEntry[] }) {
  const [filter, setFilter] = useState("ALL");
  const eventTypes = useMemo(
    () => Array.from(new Set(entries.map((entry) => entry.event_type))).sort(),
    [entries],
  );
  const filtered = filter === "ALL" ? entries : entries.filter((e) => e.event_type === filter);

  if (entries.length === 0) {
    return <Typography color="text.secondary">No timeline entries yet.</Typography>;
  }

  return (
    <Stack spacing={2}>
      <FormControl size="small" sx={{ maxWidth: 240 }}>
        <InputLabel>Filter</InputLabel>
        <Select value={filter} label="Filter" onChange={(e) => setFilter(e.target.value)}>
          <MenuItem value="ALL">All events</MenuItem>
          {eventTypes.map((type) => (
            <MenuItem key={type} value={type}>
              {type.replaceAll("_", " ")}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      {filtered.map((entry) => (
        <Box key={entry.id} sx={{ borderLeft: 3, borderColor: "primary.main", pl: 2 }}>
          <Typography fontWeight={700}>{entry.event_type.replaceAll("_", " ")}</Typography>
          <Typography variant="body2">{entry.description}</Typography>
          <Typography variant="caption" color="text.secondary">
            {formatDateTime(entry.created_at)}
          </Typography>
        </Box>
      ))}
    </Stack>
  );
}
