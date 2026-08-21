import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { alpha } from "@mui/material/styles";
import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { getErrorMessage } from "../utils/errors";
import { PremiumCard } from "../design-system";
import { colors } from "../design-system/tokens";

const loginSchema = z.object({
  username: z.string().min(1, "Enter your username"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setError(null);
    try {
      await login(values.username, values.password);
      navigate("/");
    } catch (err) {
      setError(getErrorMessage(err, "Login failed."));
    }
  });

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        p: 2,
        background: `linear-gradient(160deg, ${colors.navy.deep} 0%, ${colors.navy.primary} 42%, ${colors.blueGrey[50]} 42%)`,
      }}
    >
      <Box sx={{ width: "100%", maxWidth: 440 }}>
        <Box sx={{ mb: 3, textAlign: "center", color: "common.white" }}>
          <Typography variant="overline" sx={{ color: alpha("#FFFFFF", 0.7) }}>
            Executive Transport Platform
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 700, letterSpacing: "0.04em" }}>
            PRODRIVE
          </Typography>
          <Typography variant="body2" sx={{ color: alpha("#FFFFFF", 0.72), mt: 0.5 }}>
            Dispatcher sign in
          </Typography>
        </Box>
        <PremiumCard contentSx={{ p: 3 }}>
          <Stack spacing={2.5} component="form" onSubmit={onSubmit}>
            <Typography variant="body2" color="text.secondary">
              Sign in to manage transport operations.
            </Typography>
            {error ? <Alert severity="error">{error}</Alert> : null}
            <TextField
              label="Username"
              autoComplete="username"
              error={Boolean(errors.username)}
              helperText={errors.username?.message}
              {...register("username")}
            />
            <TextField
              label="Password"
              type="password"
              autoComplete="current-password"
              error={Boolean(errors.password)}
              helperText={errors.password?.message}
              {...register("password")}
            />
            <Button type="submit" variant="contained" size="large" disabled={isSubmitting} fullWidth>
              {isSubmitting ? "Signing in..." : "Sign in"}
            </Button>
          </Stack>
        </PremiumCard>
      </Box>
    </Box>
  );
}
