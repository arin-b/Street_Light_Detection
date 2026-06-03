import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#176b6b"
    },
    secondary: {
      main: "#a95b22"
    },
    background: {
      default: "#f6f7f8",
      paper: "#ffffff"
    },
    success: {
      main: "#26734d"
    },
    warning: {
      main: "#b7791f"
    },
    error: {
      main: "#b42318"
    }
  },
  shape: {
    borderRadius: 4
  },
  typography: {
    fontFamily: ["Inter", "Roboto", "Arial", "sans-serif"].join(","),
    h5: {
      fontWeight: 700,
      letterSpacing: 0
    },
    h6: {
      fontWeight: 700,
      letterSpacing: 0
    },
    button: {
      textTransform: "none",
      letterSpacing: 0
    }
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none"
        }
      }
    },
    MuiButton: {
      defaultProps: {
        variant: "contained"
      },
      styleOverrides: {
        root: {
          minHeight: 36
        }
      }
    },
    MuiTextField: {
      defaultProps: {
        size: "small"
      }
    }
  }
});
