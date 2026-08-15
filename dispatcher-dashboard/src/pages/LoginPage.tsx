import { Box, Button, Paper, Stack, TextField, Typography } from "@mui/material";
import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { ErrorAlert } from "../components/StatusChip";

export function LoginPage() {
  const { user, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", bgcolor: "background.default" }}>
      <Paper sx={{ p: 4, width: 420, borderRadius: 4 }}>
        <Stack spacing={2}>
          <Typography variant="h4">Control Center</Typography>
          <Typography color="text.secondary">Sign in to manage transport operations.</Typography>
          <ErrorAlert message={error} />
          <Box component="form" onSubmit={handleSubmit}>
            <Stack spacing={2}>
              <TextField label="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
              <TextField
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Button type="submit" variant="contained" disabled={busy}>
                Enter cockpit
              </Button>
            </Stack>
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}
