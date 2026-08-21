import { CssBaseline, ThemeProvider } from "@mui/material";
import { prodriveTheme } from "../design-system/theme";

export const theme = prodriveTheme;

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}
