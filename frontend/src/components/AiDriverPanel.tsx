import { useState } from "react";
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
  TextField,
  Typography,
} from "@mui/material";
import PsychologyIcon from "@mui/icons-material/Psychology";
import { useMutation } from "@tanstack/react-query";
import { aiService } from "../services/aiService";
import { ConfidenceChip } from "./ConfidenceChip";
import { ErrorAlert } from "./ErrorAlert";
import type { AISuggestion, DriverRecommendationOutput } from "../types/api";

interface AiDriverPanelProps {
  orderId: string;
  onSelectDriver?: (driverId: string) => void;
}

function asDriverOutput(output: Record<string, unknown>): DriverRecommendationOutput {
  return output as DriverRecommendationOutput;
}

export function AiDriverPanel({ orderId, onSelectDriver }: AiDriverPanelProps) {
  const [suggestion, setSuggestion] = useState<AISuggestion | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const recommendMutation = useMutation({
    mutationFn: () => aiService.recommendDriver(orderId),
    onSuccess: setSuggestion,
  });

  const approveMutation = useMutation({
    mutationFn: () => aiService.approveSuggestion(suggestion!.id),
    onSuccess: (data) => {
      setSuggestion(data);
      const recommended = asDriverOutput(data.output_json).recommended;
      if (recommended?.driver_id && onSelectDriver) {
        onSelectDriver(recommended.driver_id);
      }
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => aiService.rejectSuggestion(suggestion!.id, rejectReason || undefined),
    onSuccess: setSuggestion,
  });

  const output = suggestion ? asDriverOutput(suggestion.output_json) : null;

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} alignItems="center">
            <PsychologyIcon color="primary" />
            <Typography variant="h6">AI driver recommendation</Typography>
          </Stack>
          <Typography color="text.secondary" variant="body2">
            AI suggests a driver based on availability and compatibility. You must still assign the
            driver manually — approval records your decision only.
          </Typography>

          <Box>
            <Button
              variant="outlined"
              onClick={() => recommendMutation.mutate()}
              disabled={recommendMutation.isPending}
            >
              {recommendMutation.isPending ? "Analyzing..." : "Get recommendation"}
            </Button>
          </Box>

          {recommendMutation.isError ? <ErrorAlert error={recommendMutation.error} /> : null}

          {suggestion && output ? (
            <Stack spacing={2}>
              <Alert severity="info">
                Suggestion {suggestion.status.toLowerCase()} · confidence{" "}
                {Math.round(suggestion.confidence * 100)}%
              </Alert>
              <ConfidenceChip label="Recommendation" confidence={output.overall_confidence} />

              {output.recommended ? (
                <Box>
                  <Typography variant="subtitle1" fontWeight={600}>
                    Recommended: {output.recommended.driver_name}
                  </Typography>
                  <List dense>
                    {output.recommended.reasons.map((reason) => (
                      <ListItem key={reason} disablePadding>
                        <ListItemText primary={`• ${reason}`} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              ) : (
                <Typography color="text.secondary">No suitable driver found.</Typography>
              )}

              {output.alternatives.length ? (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Alternatives
                  </Typography>
                  {output.alternatives.map((alt) => (
                    <Typography key={alt.driver_id} variant="body2" color="text.secondary">
                      {alt.driver_name} ({Math.round(alt.confidence * 100)}%) —{" "}
                      {alt.reasons[0] ?? "See details"}
                    </Typography>
                  ))}
                </Box>
              ) : null}

              {suggestion.status === "PENDING" ? (
                <Stack direction="row" spacing={2} alignItems="center">
                  <Button
                    variant="contained"
                    onClick={() => approveMutation.mutate()}
                    disabled={approveMutation.isPending || !output.recommended}
                  >
                    Accept recommendation
                  </Button>
                  <TextField
                    label="Rejection reason"
                    size="small"
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                  />
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => rejectMutation.mutate()}
                    disabled={rejectMutation.isPending}
                  >
                    Reject
                  </Button>
                </Stack>
              ) : null}

              {approveMutation.isError ? <ErrorAlert error={approveMutation.error} /> : null}
              {rejectMutation.isError ? <ErrorAlert error={rejectMutation.error} /> : null}
              {suggestion.status === "APPROVED" ? (
                <Alert severity="success">
                  Recommendation accepted. Driver pre-selected — click Assign to confirm.
                </Alert>
              ) : null}
            </Stack>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}
