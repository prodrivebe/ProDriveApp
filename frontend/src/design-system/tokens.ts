/** ProDrive premium design tokens — single source of truth for visual language. */

export const colors = {
  navy: {
    deep: "#0F2438",
    primary: "#1B3A5F",
    mid: "#2C4A6B",
    soft: "#3D5F82",
  },
  blueGrey: {
    50: "#F4F6F9",
    100: "#E8ECF2",
    200: "#D4DCE6",
    400: "#8B95A5",
    600: "#5C6778",
    800: "#3A4454",
  },
  ivory: {
    warm: "#FAF9F6",
    paper: "#FFFFFF",
    muted: "#F5F4F0",
  },
  champagne: {
    main: "#B8A068",
    light: "#D4C498",
    muted: "rgba(184, 160, 104, 0.16)",
  },
  semantic: {
    success: "#2E7D5A",
    successMuted: "rgba(46, 125, 90, 0.12)",
    warning: "#B8860B",
    warningMuted: "rgba(184, 134, 11, 0.12)",
    error: "#B54A4A",
    errorMuted: "rgba(181, 74, 74, 0.12)",
    info: "#3D6B8C",
    infoMuted: "rgba(61, 107, 140, 0.12)",
  },
  silver: "#9AA5B4",
  slate: "#6B7788",
} as const;

export const radii = {
  xs: 6,
  sm: 8,
  md: 10,
  lg: 14,
  xl: 18,
} as const;

export const shadows = {
  none: "none",
  surface: "0 1px 2px rgba(15, 36, 56, 0.04), 0 1px 3px rgba(15, 36, 56, 0.06)",
  card: "0 2px 8px rgba(15, 36, 56, 0.06), 0 1px 2px rgba(15, 36, 56, 0.04)",
  elevated: "0 4px 16px rgba(15, 36, 56, 0.08), 0 2px 4px rgba(15, 36, 56, 0.04)",
  modal: "0 12px 40px rgba(15, 36, 56, 0.14), 0 4px 12px rgba(15, 36, 56, 0.06)",
  focus: "0 0 0 3px rgba(184, 160, 104, 0.28)",
} as const;

export const spacing = {
  page: 24,
  section: 20,
  card: 20,
  tableRow: 14,
} as const;

export const typography = {
  fontFamily: '"Inter", "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif',
  fontFamilyMono: '"IBM Plex Mono", "Consolas", "Monaco", monospace',
} as const;

export const transitions = {
  fast: "150ms cubic-bezier(0.4, 0, 0.2, 1)",
  standard: "200ms cubic-bezier(0.4, 0, 0.2, 1)",
} as const;

export const layout = {
  sidebarWidth: 248,
  topBarHeight: 64,
  contentMaxWidth: 1440,
} as const;
