import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#111111" },
    secondary: { main: "#8b0000" },
    background: { default: "#f4f1ec", paper: "#ffffff" },
  },
  typography: {
    fontFamily: '"Manrope", sans-serif',
    h4: { fontFamily: '"Cormorant Garamond", serif', fontWeight: 700 },
    h5: { fontFamily: '"Cormorant Garamond", serif', fontWeight: 700 },
    h6: { fontFamily: '"Cormorant Garamond", serif', fontWeight: 600 },
  },
  shape: { borderRadius: 16 },
});
