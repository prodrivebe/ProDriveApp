import { Alert } from "@mui/material";
import { getErrorMessage, isForbidden, isNotFound, isUnauthorized } from "../utils/errors";

export function ErrorAlert({ error }: { error: unknown }) {
  const severity = isUnauthorized(error)
    ? "warning"
    : isForbidden(error) || isNotFound(error)
      ? "info"
      : "error";

  return <Alert severity={severity}>{getErrorMessage(error)}</Alert>;
}
