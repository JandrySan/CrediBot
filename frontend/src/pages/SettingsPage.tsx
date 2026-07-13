import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";

import ApiIcon from "@mui/icons-material/Api";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CloudQueueIcon from "@mui/icons-material/CloudQueue";
import ErrorIcon from "@mui/icons-material/Error";
import ForumIcon from "@mui/icons-material/Forum";
import HelpIcon from "@mui/icons-material/Help";
import RefreshIcon from "@mui/icons-material/Refresh";
import SettingsIcon from "@mui/icons-material/Settings";
import WebhookIcon from "@mui/icons-material/Webhook";

import { API_BASE_URL, WS_BASE_URL } from "../config/api";
import { useDashboard } from "../hooks/useDashboard";

function statusColor(isOk: boolean) {
  return isOk ? "success" : "error";
}

export function SettingsPage() {
  const navigate = useNavigate();
  const { stats, loading, error } = useDashboard();
  const apiOnline = !loading && !error;

  const configItems = [
    {
      label: "API Backend",
      value: API_BASE_URL,
      icon: <ApiIcon />,
      ok: apiOnline,
      detail: apiOnline ? "Conectado" : "Sin respuesta",
    },
    {
      label: "WebSocket Dashboard",
      value: `${WS_BASE_URL}/ws/dashboard`,
      icon: <CloudQueueIcon />,
      ok: true,
      detail: "Configurado en frontend",
    },
    {
      label: "Webhook WhatsApp",
      value: `${API_BASE_URL}/webhook/whatsapp`,
      icon: <WebhookIcon />,
      ok: true,
      detail: "Usar esta ruta publica en Twilio",
    },
  ];

  const checklist = [
    {
      title: "Backend activo",
      description: "FastAPI debe responder en /health antes de probar WhatsApp.",
      done: apiOnline,
    },
    {
      title: "Twilio Sandbox",
      description: "When a message comes in debe apuntar a /webhook/whatsapp con POST.",
      done: true,
    },
    {
      title: "Audio opcional",
      description: "Para notas de voz, AUDIO_REPLY_ENABLED y URL publica deben estar listos.",
      done: true,
    },
    {
      title: "FAQs cargadas",
      description: "Mantener politicas y requisitos actualizados mejora las respuestas.",
      done: true,
    },
  ];

  return (
    <Stack spacing={3}>
      <Stack
        direction={{ xs: "column", md: "row" }}
        sx={{ justifyContent: "space-between", gap: 2 }}
      >
        <Box>
          <Typography variant="h4">Configuracion</Typography>
          <Typography color="text.secondary">
            Estado de conexiones y parametros clave para operar CrediBot.
          </Typography>
        </Box>

        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={() => window.location.reload()}
        >
          Recargar estado
        </Button>
      </Stack>

      {error && (
        <Alert severity="error">
          No se pudo conectar con el backend. Revisa que FastAPI este activo.
        </Alert>
      )}

      <Grid container spacing={2.5}>
        {configItems.map((item) => (
          <Grid size={{ xs: 12, lg: 4 }} key={item.label}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Stack spacing={2}>
                  <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                    <Box
                      sx={{
                        width: 42,
                        height: 42,
                        borderRadius: 2,
                        bgcolor: "#CCFBF1",
                        color: "#0F766E",
                        display: "grid",
                        placeItems: "center",
                      }}
                    >
                      {item.icon}
                    </Box>
                    <Chip
                      size="small"
                      color={statusColor(item.ok)}
                      label={item.detail}
                    />
                  </Stack>
                  <Box>
                    <Typography sx={{ fontWeight: 800 }}>{item.label}</Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ overflowWrap: "anywhere" }}
                    >
                      {item.value}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, md: 7 }}>
          <Card>
            <CardContent>
              <Stack spacing={2.25}>
                <Box>
                  <Typography variant="h6">Checklist operativo</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Puntos minimos para que WhatsApp, dashboard y audio funcionen.
                  </Typography>
                </Box>

                {checklist.map((item) => (
                  <Stack key={item.title} spacing={1}>
                    <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                      {item.done ? (
                        <CheckCircleIcon color="success" />
                      ) : (
                        <ErrorIcon color="error" />
                      )}
                      <Box>
                        <Typography sx={{ fontWeight: 800 }}>
                          {item.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {item.description}
                        </Typography>
                      </Box>
                    </Stack>
                    <Divider />
                  </Stack>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent>
              <Stack spacing={2.25}>
                <Box>
                  <Typography variant="h6">Resumen del sistema</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Lectura actual del dashboard desde el backend.
                  </Typography>
                </Box>

                <Stack spacing={1.5}>
                  <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                    <Typography color="text.secondary">Clientes</Typography>
                    <Typography sx={{ fontWeight: 900 }}>
                      {stats?.customers ?? "-"}
                    </Typography>
                  </Stack>
                  <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                    <Typography color="text.secondary">Conversaciones</Typography>
                    <Typography sx={{ fontWeight: 900 }}>
                      {stats?.conversations ?? "-"}
                    </Typography>
                  </Stack>
                  <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                    <Typography color="text.secondary">Activas</Typography>
                    <Typography sx={{ fontWeight: 900 }}>
                      {stats?.active_conversations ?? "-"}
                    </Typography>
                  </Stack>
                </Stack>

                <Divider />

                <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                  <Button
                    variant="outlined"
                    startIcon={<ForumIcon />}
                    onClick={() => navigate("/conversaciones")}
                  >
                    Conversaciones
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<HelpIcon />}
                    onClick={() => navigate("/faqs")}
                  >
                    FAQs
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<SettingsIcon />}
                    onClick={() => navigate("/analitica")}
                  >
                    Analitica
                  </Button>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}
