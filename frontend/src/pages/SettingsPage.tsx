import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import ApiIcon from "@mui/icons-material/Api";
import CloudQueueIcon from "@mui/icons-material/CloudQueue";
import RefreshIcon from "@mui/icons-material/Refresh";
import WebhookIcon from "@mui/icons-material/Webhook";

import { API_BASE_URL, WS_BASE_URL } from "../config/api";
import { ConnectionCards, SettingsDetails } from "../features/settings/SettingsPanels";
import { useDashboard } from "../hooks/useDashboard";

export function SettingsPage() {
  const { stats, loading, error } = useDashboard();
  const apiOnline = !loading && !error;
  const connections = [
    { label: "API Backend", value: API_BASE_URL, icon: <ApiIcon />, ok: apiOnline, detail: apiOnline ? "Conectado" : "Sin respuesta" },
    { label: "WebSocket Dashboard", value: `${WS_BASE_URL}/ws/dashboard`, icon: <CloudQueueIcon />, ok: true, detail: "Configurado" },
    { label: "Webhook WhatsApp", value: `${API_BASE_URL}/webhook/whatsapp`, icon: <WebhookIcon />, ok: true, detail: "Ruta disponible" },
  ];
  const checklist = [
    { title: "Backend activo", description: "FastAPI debe responder en /api/health antes de probar WhatsApp.", done: apiOnline },
    { title: "Twilio Sandbox", description: "When a message comes in debe apuntar al webhook con POST.", done: true },
    { title: "Audio opcional", description: "Para notas de voz, activa el audio y configura la URL pública.", done: true },
    { title: "FAQs cargadas", description: "Mantener políticas y requisitos actualizados mejora las respuestas.", done: true },
  ];

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: "column", md: "row" }} sx={{ justifyContent: "space-between", gap: 2 }}>
        <Box>
          <Typography variant="h4">Configuración</Typography>
          <Typography color="text.secondary">Estado de conexiones y parámetros clave para operar CrediBot.</Typography>
        </Box>
        <Button variant="contained" startIcon={<RefreshIcon />} onClick={() => window.location.reload()}>Recargar estado</Button>
      </Stack>
      {error && <Alert severity="error">No se pudo conectar con el backend. Revisa que FastAPI esté activo.</Alert>}
      <ConnectionCards items={connections} />
      <SettingsDetails checklist={checklist} stats={stats} />
    </Stack>
  );
}
