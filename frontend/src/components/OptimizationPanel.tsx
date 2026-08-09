import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { aiService } from "../services/aiService";
import { planningService } from "../services/planningService";
import { ErrorAlert } from "./ErrorAlert";
import type { OptimizationResponse } from "../types/api";

interface OptimizationPanelProps {
  orderId: string;
  onOptimized: (result: OptimizationResponse) => void;
  onApproved?: () => void;
}

export function OptimizationPanel({ orderId, onOptimized, onApproved }: OptimizationPanelProps) {
  const optimizeMutation = useMutation({
    mutationFn: () => planningService.optimize(orderId),
    onSuccess: onOptimized,
  });

  const approveMutation = useMutation({
    mutationFn: (suggestionId: string) => aiService.approveSuggestion(suggestionId),
  });

  const rejectMutation = useMutation({
    mutationFn: (suggestionId: string) => aiService.rejectSuggestion(suggestionId, "Rejected from loading board"),
  });

  const result = optimizeMutation.data;

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6">Loading optimization</Typography>
          <Typography variant="body2" color="text.secondary">
            AI recommends positions and sequences. Approval is required before the plan is saved.
          </Typography>
          <Button
            variant="contained"
            onClick={() => optimizeMutation.mutate()}
            disabled={optimizeMutation.isPending}
          >
            {optimizeMutation.isPending ? "Optimizing..." : "Generate recommendation"}
          </Button>
          {optimizeMutation.isError ? <ErrorAlert error={optimizeMutation.error} /> : null}
          {result ? (
            <Stack spacing={1}>
              <Alert severity="info">
                Confidence {Math.round(result.confidence * 100)}% · status {result.status}
              </Alert>
              <List dense>
                {result.reasoning.map((line) => (
                  <ListItem key={line} disablePadding>
                    <ListItemText primary={`• ${line}`} />
                  </ListItem>
                ))}
              </List>
              <Stack direction="row" spacing={1}>
                <Button
                  variant="contained"
                  color="success"
                  disabled={approveMutation.isPending}
                  onClick={() =>
                    approveMutation.mutate(result.suggestion_id, {
                      onSuccess: () => onApproved?.(),
                    })
                  }
                >
                  Approve & apply
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  onClick={() => rejectMutation.mutate(result.suggestion_id)}
                >
                  Reject
                </Button>
              </Stack>
            </Stack>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}
