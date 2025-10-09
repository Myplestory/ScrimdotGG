import React from "react";
import CircularProgress from "@mui/material/CircularProgress";
import { Box } from "@mui/material";
import { useMode } from "../theme";

const LoadingScreen = () => {
  const [theme, colorMode] = useMode();
  return (
    <Box
      sx={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: theme.palette.primary, // Use rgba to set the opacity to 0
        zIndex: 9999, // Make sure it's on top of other elements
        overflow: false,
      }}
    >
      <CircularProgress />
    </Box>
  );
};

export default LoadingScreen;