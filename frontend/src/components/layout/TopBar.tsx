import LogoutIcon from "@mui/icons-material/Logout";
import { AppBar, Avatar, Box, Chip, IconButton, Toolbar, Tooltip, Typography } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthService } from "../../services/auth.service";

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  "/panel": {
    title: "Panel operativo",
    subtitle: "Resumen de conversaciones, creditos e IA",
  },
  "/conversaciones": {
    title: "Panel de asesor",
    subtitle: "Gestion de conversaciones, creditos e IA",
  },
  "/faqs": {
    title: "Administracion de FAQs",
    subtitle: "Politicas, requisitos y respuestas frecuentes",
  },
  "/analitica": {
    title: "Analitica",
    subtitle: "Indicadores de atencion y precalificacion",
  },
  "/configuracion": {
    title: "Configuracion",
    subtitle: "Estado de conexiones e integracion WhatsApp",
  },
};

export function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const page = pageTitles[location.pathname] ?? pageTitles["/conversaciones"];

  function logout() {
    AuthService.logout();
    navigate("/login");
  }

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
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            {page.title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {page.subtitle}
          </Typography>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Chip label="En linea" color="success" size="small" />
          <Avatar sx={{ bgcolor: "#0F766E", fontWeight: 800 }}>A</Avatar>
          <Tooltip title="Cerrar sesion">
            <IconButton aria-label="Cerrar sesion" onClick={logout}>
              <LogoutIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
