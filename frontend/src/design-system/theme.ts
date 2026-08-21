import { alpha, createTheme, type ThemeOptions } from "@mui/material/styles";
import { colors, radii, shadows, typography, transitions } from "./tokens";

declare module "@mui/material/styles" {
  interface Palette {
    accent: {
      main: string;
      light: string;
      muted: string;
      contrastText: string;
    };
    surface: {
      page: string;
      card: string;
      elevated: string;
    };
  }
  interface PaletteOptions {
    accent?: {
      main: string;
      light: string;
      muted: string;
      contrastText: string;
    };
    surface?: {
      page: string;
      card: string;
      elevated: string;
    };
  }
}

export const prodriveThemeOptions: ThemeOptions = {
  palette: {
    mode: "light",
    primary: {
      main: colors.navy.primary,
      dark: colors.navy.deep,
      light: colors.navy.soft,
      contrastText: colors.ivory.paper,
    },
    secondary: {
      main: colors.blueGrey[600],
      light: colors.blueGrey[400],
      dark: colors.blueGrey[800],
      contrastText: colors.ivory.paper,
    },
    accent: {
      main: colors.champagne.main,
      light: colors.champagne.light,
      muted: colors.champagne.muted,
      contrastText: colors.navy.deep,
    },
    surface: {
      page: colors.blueGrey[50],
      card: colors.ivory.paper,
      elevated: colors.ivory.warm,
    },
    background: {
      default: colors.blueGrey[50],
      paper: colors.ivory.paper,
    },
    text: {
      primary: colors.navy.deep,
      secondary: colors.slate,
      disabled: colors.silver,
    },
    divider: colors.blueGrey[200],
    success: {
      main: colors.semantic.success,
      light: colors.semantic.successMuted,
    },
    warning: {
      main: colors.semantic.warning,
      light: colors.semantic.warningMuted,
    },
    error: {
      main: colors.semantic.error,
      light: colors.semantic.errorMuted,
    },
    info: {
      main: colors.semantic.info,
      light: colors.semantic.infoMuted,
    },
    action: {
      hover: alpha(colors.navy.primary, 0.04),
      selected: alpha(colors.navy.primary, 0.08),
      focus: alpha(colors.champagne.main, 0.2),
    },
  },
  typography: {
    fontFamily: typography.fontFamily,
    h1: { fontSize: "2rem", fontWeight: 600, letterSpacing: "-0.02em", lineHeight: 1.25 },
    h2: { fontSize: "1.625rem", fontWeight: 600, letterSpacing: "-0.015em", lineHeight: 1.3 },
    h3: { fontSize: "1.375rem", fontWeight: 600, letterSpacing: "-0.01em", lineHeight: 1.35 },
    h4: { fontSize: "1.25rem", fontWeight: 600, letterSpacing: "-0.01em", lineHeight: 1.4 },
    h5: { fontSize: "1.125rem", fontWeight: 600, lineHeight: 1.45 },
    h6: { fontSize: "1rem", fontWeight: 600, lineHeight: 1.5 },
    subtitle1: { fontSize: "0.9375rem", fontWeight: 500, lineHeight: 1.5 },
    subtitle2: { fontSize: "0.875rem", fontWeight: 500, lineHeight: 1.5, color: colors.slate },
    body1: { fontSize: "0.9375rem", lineHeight: 1.6 },
    body2: { fontSize: "0.875rem", lineHeight: 1.55, color: colors.slate },
    caption: {
      fontSize: "0.75rem",
      lineHeight: 1.45,
      color: colors.silver,
      letterSpacing: "0.01em",
    },
    overline: {
      fontSize: "0.6875rem",
      fontWeight: 600,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      color: colors.silver,
    },
    button: { fontWeight: 600, letterSpacing: "0.02em", textTransform: "none" },
  },
  shape: { borderRadius: radii.md },
  shadows: [
    "none",
    shadows.surface,
    shadows.card,
    shadows.card,
    shadows.elevated,
    shadows.elevated,
    shadows.elevated,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
    shadows.modal,
  ],
  transitions: {
    duration: { shortest: 150, shorter: 180, short: 200, standard: 250 },
    easing: { easeInOut: transitions.standard },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: colors.blueGrey[50],
          WebkitFontSmoothing: "antialiased",
          MozOsxFontSmoothing: "grayscale",
        },
        "#root": { minHeight: "100vh" },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          borderRadius: radii.sm,
          minHeight: 40,
          padding: "8px 18px",
          transition: transitions.fast,
        },
        contained: {
          background: `linear-gradient(180deg, ${colors.navy.mid} 0%, ${colors.navy.primary} 100%)`,
          boxShadow: shadows.surface,
          "&:hover": {
            background: `linear-gradient(180deg, ${colors.navy.primary} 0%, ${colors.navy.deep} 100%)`,
            boxShadow: shadows.card,
          },
        },
        containedPrimary: {
          borderTop: `1px solid ${alpha(colors.champagne.light, 0.35)}`,
        },
        outlined: {
          borderColor: colors.blueGrey[200],
          color: colors.navy.primary,
          backgroundColor: colors.ivory.paper,
          "&:hover": {
            borderColor: colors.navy.soft,
            backgroundColor: colors.ivory.warm,
          },
        },
        text: {
          color: colors.navy.mid,
          "&:hover": { backgroundColor: alpha(colors.navy.primary, 0.05) },
        },
        sizeSmall: { minHeight: 34, padding: "6px 14px", fontSize: "0.8125rem" },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          borderRadius: radii.sm,
          transition: transitions.fast,
          "&:hover": { backgroundColor: alpha(colors.navy.primary, 0.06) },
        },
      },
    },
    MuiTextField: {
      defaultProps: { variant: "outlined", size: "small" },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: radii.sm,
          backgroundColor: colors.ivory.warm,
          transition: transitions.fast,
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: colors.blueGrey[200],
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: colors.blueGrey[400],
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: colors.navy.primary,
            borderWidth: 1,
          },
          "&.Mui-focused": {
            boxShadow: shadows.focus,
            backgroundColor: colors.ivory.paper,
          },
        },
        input: { fontSize: "0.9375rem", padding: "10px 12px" },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          fontSize: "0.875rem",
          color: colors.slate,
          "&.Mui-focused": { color: colors.navy.primary },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: { borderRadius: radii.sm },
      },
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: { marginTop: 4, fontSize: "0.75rem" },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          borderRadius: radii.lg,
          border: `1px solid ${colors.blueGrey[200]}`,
          boxShadow: shadows.card,
          backgroundImage: "none",
        },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: { backgroundImage: "none" },
        outlined: {
          borderRadius: radii.lg,
          border: `1px solid ${colors.blueGrey[200]}`,
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          borderRadius: radii.lg,
          border: `1px solid ${colors.blueGrey[200]}`,
          boxShadow: shadows.surface,
          overflow: "hidden",
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: colors.ivory.warm,
          "& .MuiTableCell-head": {
            fontWeight: 600,
            fontSize: "0.75rem",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: colors.slate,
            borderBottom: `1px solid ${colors.blueGrey[200]}`,
            paddingTop: 14,
            paddingBottom: 14,
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${alpha(colors.blueGrey[200], 0.75)}`,
          paddingTop: 14,
          paddingBottom: 14,
          fontSize: "0.875rem",
        },
        body: { color: colors.navy.deep },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: transitions.fast,
          "&:hover": { backgroundColor: alpha(colors.navy.primary, 0.03) },
          "&.Mui-selected": {
            backgroundColor: alpha(colors.champagne.main, 0.08),
            "&:hover": { backgroundColor: alpha(colors.champagne.main, 0.12) },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: radii.xs,
          fontWeight: 600,
          fontSize: "0.6875rem",
          letterSpacing: "0.03em",
          height: 24,
        },
        sizeSmall: { height: 22, fontSize: "0.625rem" },
        filled: { border: "1px solid transparent" },
        outlined: { borderColor: colors.blueGrey[200] },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: radii.xl,
          boxShadow: shadows.modal,
          border: `1px solid ${colors.blueGrey[200]}`,
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          fontSize: "1.125rem",
          fontWeight: 600,
          paddingBottom: 8,
          color: colors.navy.deep,
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: { paddingTop: "12px !important" },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: "16px 24px 20px",
          borderTop: `1px solid ${colors.blueGrey[100]}`,
          gap: 8,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: radii.sm },
        standardSuccess: { backgroundColor: colors.semantic.successMuted },
        standardWarning: { backgroundColor: colors.semantic.warningMuted },
        standardError: { backgroundColor: colors.semantic.errorMuted },
        standardInfo: { backgroundColor: colors.semantic.infoMuted },
      },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: { borderRight: "none" },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: radii.sm,
          margin: "2px 10px",
          paddingTop: 10,
          paddingBottom: 10,
          transition: transitions.fast,
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: { height: 3, borderRadius: 2 },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          borderRadius: radii.xs,
          fontSize: "0.75rem",
          backgroundColor: colors.navy.deep,
        },
      },
    },
  },
};

export const prodriveTheme = createTheme(prodriveThemeOptions);
