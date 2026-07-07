import { AppBar, Avatar, Box, Toolbar, Typography } from "@mui/material";

export function TopBar() {
  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        background: "white",
        color: "#1f2937",
        borderBottom: "1px solid #e5e7eb",
      }}
    >
      <Toolbar sx={{ justifyContent: "space-between" }}>
        <Box>
          <Typography variant="h6" fontWeight={700}>
            Panel de Asesor
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Monitoreo de conversaciones y precalificaciones
          </Typography>
        </Box>

        <Avatar sx={{ bgcolor: "#128C7E" }}>A</Avatar>
      </Toolbar>
    </AppBar>
  );
}