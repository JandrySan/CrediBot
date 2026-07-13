import { useMemo } from "react";
import { useNavigate } from "react-router-dom";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from "@mui/material";

import AssessmentIcon from "@mui/icons-material/Assessment";
import ChatIcon from "@mui/icons-material/Chat";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ForumIcon from "@mui/icons-material/Forum";
import HelpIcon from "@mui/icons-material/Help";
import SettingsIcon from "@mui/icons-material/Settings";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import WarningIcon from "@mui/icons-material/Warning";

import { useConversations } from "../hooks/useConversations";
import { useDashboard } from "../hooks/useDashboard";

function percent(value: number, total: number) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}

export function OverviewPage() {
  const navigate = useNavigate();
  const { stats, loading, error } = useDashboard();
  const { data: conversations = [], isLoading: conversationsLoading } =
    useConversations();

  const recentConversations = useMemo(
    () => conversations.slice(0, 5),
    [conversations]
  );

  const resolvedTotal = (stats?.preapproved ?? 0) + (stats?.observed ?? 0);
  const preapprovedRate = percent(stats?.preapproved ?? 0, resolvedTotal);

  if (loading || conversationsLoading) {
    return (
      <Box sx={{ display: "grid", placeItems: "center", minHeight: 420 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">No se pudo conectar con el backend.</Alert>;
  }

  const cards = [
    {
      label: "Conversaciones",
      value: stats?.conversations ?? 0,
      helper: "Visibles en dashboard",
      icon: <ForumIcon />,
    },
    {
      label: "Activas",
      value: stats?.active_conversations ?? 0,
      helper: "Atendidas por bot",
      icon: <ChatIcon />,
    },
    {
      label: "Derivadas",
      value: stats?.handoff_conversations ?? 0,
      helper: "Esperando asesor",
      icon: <SupportAgentIcon />,
    },
    {
      label: "Preaprobados",
      value: stats?.preapproved ?? 0,
      helper: `${preapprovedRate}% de casos evaluados`,
      icon: <CheckCircleIcon />,
    },
  ];

  return (
    <Stack spacing={3}>
      <Stack
        direction={{ xs: "column", md: "row" }}
        sx={{ justifyContent: "space-between", gap: 2 }}
      >
        <Box>
          <Typography variant="h4">Panel operativo</Typography>
          <Typography color="text.secondary">
            Resumen rapido de atencion, precalificaciones y estado del sistema.
          </Typography>
        </Box>

        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
          <Button
            variant="contained"
            startIcon={<ChatIcon />}
            onClick={() => navigate("/conversaciones")}
          >
            Ver conversaciones
          </Button>
          <Button
            variant="outlined"
            startIcon={<AssessmentIcon />}
            onClick={() => navigate("/analitica")}
          >
            Analitica
          </Button>
        </Stack>
      </Stack>

      <Grid container spacing={2.5}>
        {cards.map((card) => (
          <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={card.label}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                  <Box>
                    <Typography color="text.secondary" sx={{ fontWeight: 700 }}>
                      {card.label}
                    </Typography>
                    <Typography variant="h3" sx={{ fontWeight: 900 }}>
                      {card.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {card.helper}
                    </Typography>
                  </Box>
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
                    {card.icon}
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <Card>
            <CardContent>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="h6">Actividad reciente</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ultimas conversaciones visibles para seguimiento operativo.
                  </Typography>
                </Box>

                {recentConversations.map((conversation) => (
                  <Stack
                    key={conversation.conversation_id}
                    direction={{ xs: "column", sm: "row" }}
                    sx={{
                      alignItems: { xs: "flex-start", sm: "center" },
                      justifyContent: "space-between",
                      gap: 1.5,
                      py: 1.25,
                      borderBottom: "1px solid #E2E8F0",
                    }}
                  >
                    <Box>
                      <Typography sx={{ fontWeight: 800 }}>
                        {conversation.full_name || conversation.phone_number}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {conversation.phone_number}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                      <Chip size="small" label={conversation.status} />
                      <Chip
                        size="small"
                        color={
                          conversation.credit_result === "PREAPROBADO"
                            ? "success"
                            : conversation.credit_result === "OBSERVADO"
                              ? "warning"
                              : "default"
                        }
                        label={conversation.credit_result || "Pendiente"}
                      />
                    </Stack>
                  </Stack>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent>
              <Stack spacing={2.25}>
                <Box>
                  <Typography variant="h6">Salud del flujo</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Indicadores basados en las conversaciones actuales.
                  </Typography>
                </Box>

                <Box>
                  <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                    <Typography variant="body2">Preaprobacion</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 800 }}>
                      {preapprovedRate}%
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="determinate"
                    value={preapprovedRate}
                    sx={{ mt: 1, height: 8, borderRadius: 1 }}
                  />
                </Box>

                <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                  <Button
                    variant="outlined"
                    startIcon={<HelpIcon />}
                    onClick={() => navigate("/faqs")}
                  >
                    Revisar FAQs
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<SettingsIcon />}
                    onClick={() => navigate("/configuracion")}
                  >
                    Configuracion
                  </Button>
                  <Button
                    variant="outlined"
                    color="warning"
                    startIcon={<WarningIcon />}
                    onClick={() => navigate("/analitica")}
                  >
                    Ver observados
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
