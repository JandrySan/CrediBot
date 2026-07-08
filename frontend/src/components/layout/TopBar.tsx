import { AppBar, Avatar, Box, Chip, Toolbar, Typography } from "@mui/material";

export function TopBar() {
  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        background: "rgba(255,255,255,0.88)",
        backdropFilter: "blur(12px)",
        color: "#0F172A",
        borderBottom: "1px solid #E2E8F0",
      }}
    >
      <Toolbar sx={{ justifyContent: "space-between", minHeight: 72 }}>
        <Box>
          <Typography variant="h6" fontWeight={800}>
            Panel de Asesor
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Gestión de conversaciones, créditos e IA
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" gap={2}>
          <Chip label="En línea" color="success" size="small" />
          <Avatar sx={{ bgcolor: "#0F766E", fontWeight: 800 }}>A</Avatar>
        </Box>
      </Toolbar>
    </AppBar>
  );
}