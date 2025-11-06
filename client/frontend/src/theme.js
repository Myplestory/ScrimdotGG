import { createContext, useState, useMemo } from "react";
import { createTheme } from "@mui/material/styles";

// color design tokens export - VALORANT INSPIRED THEME
export const tokens = (mode) => ({
  ...(mode === "dark"
    ? {
        grey: {
          100: "#ececec",
          200: "#d4d4d4",
          300: "#a8a8a8",
          400: "#7c7c7c",
          500: "#505050",
          600: "#3c3c3c",
          700: "#282828",
          800: "#1a1a1a",
          900: "#0d0d0d",
        },
        primary: {
          100: "#2a2a2a",
          200: "#232323",
          300: "#1c1c1c",
          400: "#151515", // Card backgrounds
          500: "#0f0f0f", // Main background - almost black
          600: "#0a0a0a",
          700: "#060606",
          800: "#030303",
          900: "#000000",
        },
        // Valorant Red - Main accent
        redAccent: {
          100: "#ffe5e8",
          200: "#ffccd1",
          300: "#ffb3ba",
          400: "#ff99a3",
          500: "#FF4655", // Signature Valorant red
          600: "#ff1f31",
          700: "#e6001a",
          800: "#b30014",
          900: "#80000e",
        },
        // Green for success states
        greenAccent: {
          100: "#e6f9f0",
          200: "#b3ecda",
          300: "#80dfc3",
          400: "#4dd2ad",
          500: "#1ac996",
          600: "#15a077",
          700: "#107759",
          800: "#0b4e3a",
          900: "#06251c",
        },
        // Subtle accent for highlights
        greyAccent: {
          100: "#f5f5f5",
          200: "#e8e8e8",
          300: "#d1d1d1",
          400: "#b4b4b4",
          500: "#6e6e6e", // Muted grey for secondary elements
          600: "#525252",
          700: "#3a3a3a",
          800: "#242424",
          900: "#121212",
        },
        // Keeping for compatibility
        seance: {
          DEFAULT: '#FF4655',
          50: '#ffe5e8',
          100: '#ffccd1',
          200: '#ffb3ba',
          300: '#ff99a3',
          400: '#ff809c',
          500: '#FF4655',
          600: '#ff1f31',
          700: '#e6001a',
          800: '#b30014',
          900: '#80000e'
        },
        blueAccent: {
          100: "#e6f0ff",
          200: "#cce0ff",
          300: "#99c2ff",
          400: "#66a3ff",
          500: "#3385ff",
          600: "#0066ff",
          700: "#0052cc",
          800: "#003d99",
          900: "#002966",
        },
      }
    : {
        // Light mode (inverted)
        grey: {
          100: "#0d0d0d",
          200: "#1a1a1a",
          300: "#282828",
          400: "#3c3c3c",
          500: "#505050",
          600: "#7c7c7c",
          700: "#a8a8a8",
          800: "#d4d4d4",
          900: "#ececec",
        },
        primary: {
          100: "#000000",
          200: "#030303",
          300: "#060606",
          400: "#0a0a0a",
          500: "#0f0f0f",
          600: "#151515",
          700: "#1c1c1c",
          800: "#232323",
          900: "#2a2a2a",
        },
        redAccent: {
          100: "#80000e",
          200: "#b30014",
          300: "#e6001a",
          400: "#ff1f31",
          500: "#FF4655",
          600: "#ff99a3",
          700: "#ffb3ba",
          800: "#ffccd1",
          900: "#ffe5e8",
        },
        greenAccent: {
          100: "#06251c",
          200: "#0b4e3a",
          300: "#107759",
          400: "#15a077",
          500: "#1ac996",
          600: "#4dd2ad",
          700: "#80dfc3",
          800: "#b3ecda",
          900: "#e6f9f0",
        },
        greyAccent: {
          100: "#121212",
          200: "#242424",
          300: "#3a3a3a",
          400: "#525252",
          500: "#6e6e6e",
          600: "#b4b4b4",
          700: "#d1d1d1",
          800: "#e8e8e8",
          900: "#f5f5f5",
        },
        seance: {
          DEFAULT: '#FF4655',
          50: '#80000e',
          100: '#b30014',
          200: '#e6001a',
          300: '#ff1f31',
          400: '#FF4655',
          500: '#ff809c',
          600: '#ff99a3',
          700: '#ffb3ba',
          800: '#ffccd1',
          900: '#ffe5e8'
        },
        blueAccent: {
          100: "#002966",
          200: "#003d99",
          300: "#0052cc",
          400: "#0066ff",
          500: "#3385ff",
          600: "#66a3ff",
          700: "#99c2ff",
          800: "#cce0ff",
          900: "#e6f0ff",
        },
      }),
});

// mui theme settings
export const themeSettings = (mode) => {
  const colors = tokens(mode);
  return {
    palette: {
      mode: mode,
      ...(mode === "dark"
        ? {
            // palette values for dark mode - VALORANT THEME
            primary: {
              main: colors.primary[500], // Almost black background
              light: colors.primary[400], // Card backgrounds
              dark: colors.primary[600],
            },
            secondary: {
              main: colors.redAccent[500], // Valorant red as main accent
              light: colors.redAccent[400],
              dark: colors.redAccent[600],
            },
            error: {
              main: colors.redAccent[500],
            },
            warning: {
              main: "#FFA726",
            },
            info: {
              main: colors.greyAccent[500],
            },
            success: {
              main: colors.greenAccent[500],
            },
            neutral: {
              dark: colors.grey[700],
              main: colors.grey[500],
              light: colors.grey[300],
            },
            background: {
              default: colors.primary[500], // Main dark background
              paper: colors.primary[400], // Card background
              dark: colors.grey[900], // Darker sections
            },
            text: {
              primary: colors.grey[100], // White text
              secondary: colors.grey[400], // Muted text
            },
          }
        : {
            // palette values for light mode
            primary: {
              main: colors.primary[100],
            },
            secondary: {
              main: colors.seance[500],
            },
            neutral: {
              dark: colors.grey[700],
              main: colors.grey[500],
              light: colors.grey[100],
            },
            background: {
              default: "#fcfcfc",
            },
          }),
    },
    typography: {
      fontFamily: ["Source Sans Pro", "sans-serif"].join(","),
      fontSize: 12,
      h1: {
        fontFamily: ["Source Sans Pro", "sans-serif"].join(","),
        fontSize: 40,
      },
      h2: {
        fontFamily: ["Source Sans Pro", "sans-serif"].join(","),
        fontSize: 32,
      },
      h3: {
        fontFamily: ["Source Sans Pro", "sans-serif"].join(","),
        fontSize: 24,
      },
      h4: {
        fontFamily: ["Source Sans Pro", "sans-serif"].join(","),
        fontSize: 20,
      },
      h5: {
        fontFamily: ["Source Sans Pro", "sans-serif"].join(","),
        fontSize: 16,
      },
      h6: {
        fontFamily: ["Source Sans Pro", "sans-serif"].join(","),
        fontSize: 14,
      },
    },
    components: {
      MuiSelect: {
        styleOverrides: {
          root: {
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: mode === 'dark' ? colors.redAccent[500] : colors.redAccent[500],
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: mode === 'dark' ? colors.redAccent[400] : colors.redAccent[400],
            },
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: mode === 'dark' ? colors.redAccent[500] : colors.redAccent[500],
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: mode === 'dark' ? colors.redAccent[400] : colors.redAccent[400],
            },
          },
        },
      },
      MuiInputLabel: {
        styleOverrides: {
          root: {
            '&.Mui-focused': {
              color: mode === 'dark' ? colors.redAccent[500] : colors.redAccent[500],
            },
          },
        },
      },
      MuiMenuItem: {
        styleOverrides: {
          root: {
            '&.Mui-selected': {
              backgroundColor: mode === 'dark' ? `${colors.redAccent[500]}20` : `${colors.redAccent[500]}20`,
              '&:hover': {
                backgroundColor: mode === 'dark' ? `${colors.redAccent[500]}30` : `${colors.redAccent[500]}30`,
              },
            },
            '&:hover': {
              backgroundColor: mode === 'dark' ? `${colors.redAccent[500]}10` : `${colors.redAccent[500]}10`,
            },
          },
        },
      },
    },
  };
};

// context for color mode
export const ColorModeContext = createContext({
  toggleColorMode: () => {},
});

export const useMode = () => {
  const [mode, setMode] = useState("dark");

  const colorMode = useMemo(
    () => ({
      toggleColorMode: () =>
        setMode((prev) => (prev === "light" ? "dark" : "light")),
    }),
    []
  );

  const theme = useMemo(() => createTheme(themeSettings(mode)), [mode]);
  return [theme, colorMode];
};