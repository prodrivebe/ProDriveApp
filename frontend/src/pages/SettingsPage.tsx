import { Alert, Card, CardContent, Stack, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";
import { apiGet } from "../services/apiClient";
import { usePermissions } from "../hooks/usePermissions";
import type { CompanySettings } from "../types/api";
import { LoadingState } from "../components/LoadingState";
import { ErrorAlert } from "../components/ErrorAlert";

export function SettingsPage() {
  const { canManageSettings } = usePermissions();

  const settingsQuery = useQuery({
    queryKey: ["company-settings"],
    queryFn: () => apiGet<CompanySettings>("/companies/settings"),
    enabled: canManageSettings,
  });

  if (!canManageSettings) {
    return <Navigate to="/" replace />;
  }

  if (settingsQuery.isLoading) return <LoadingState />;
  if (settingsQuery.isError) return <ErrorAlert error={settingsQuery.error} />;

  const settings = settingsQuery.data!;

  return (
    <Stack spacing={3}>
      <Typography variant="h4" fontWeight={700}>
        Settings
      </Typography>
      <Alert severity="info">Company settings are read-only in Sprint 7. Admin updates will arrive in a later sprint.</Alert>
      <Card>
        <CardContent>
          <Typography>Timezone: {settings.timezone}</Typography>
          <Typography>Default currency: {settings.default_currency}</Typography>
          <Typography>Require vehicle photos: {settings.require_vehicle_photos ? "Yes" : "No"}</Typography>
          <Typography>Primary color: {settings.primary_color}</Typography>
        </CardContent>
      </Card>
    </Stack>
  );
}
