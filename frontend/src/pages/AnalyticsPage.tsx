import { useMemo } from "react";
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from "@mui/material";

import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import ForumIcon from "@mui/icons-material/Forum";
import QueryStatsIcon from "@mui/icons-material/QueryStats";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import WarningIcon from "@mui/icons-material/Warning";

import { useConversations } from "../hooks/useConversations";
import { useDashboard } from "../hooks/useDashboard";
import type { Conversation } from "../types/conversation";

function countWhere(
  conversations: Conversation[],
  predicate: (conversation: Conversation) => boolean
) {
  return conversations.filter(predicate).length;
}

function percent(value: number, total: number) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}

function moneyAverage(values: Array<number | null>) {
  const cleanValues = values.filter((value): value is number => value !== null);
  if (!cleanValues.length) return 0;
  return Math.round(
    cleanValues.reduce((total, value) => total + value, 0) / cleanValues.length
  );
}

export function AnalyticsPage() {
  const { stats, loading, error } = useDashboard();
  const { data: conversations = [], isLoading, isError } = useConversations();

  const metrics = useMemo(() => {
    const total = conversations.length;
    const active = countWhere(
      conversations,
      (conversation) => conversation.status === "ACTIVE"
    );
    const handoff = countWhere(
      conversations,
      (conversation) =>
        conversation.status === "HANDOFF" ||
        conversation.status === "MANOS LIBRES"
    );
    const closed = countWhere(
      conversations,
      (conversation) => conversation.status === "CLOSED"
    );
    const preapproved = countWhere(
      conversations,
      (conversation) => conversation.credit_result === "PREAPROBADO"
    );
    const observed = countWhere(
      conversations,
      (conversation) => conversation.credit_result === "OBSERVADO"
    );
    const pending = countWhere(
      conversations,
      (conversation) => !conversation.credit_result
    );
    const evaluated = preapproved + observed;

    return {
      total,
      active,
      handoff,
      closed,
      preapproved,
      observed,
      pending,
      evaluated,
      preapprovedRate: percent(preapproved, evaluated),
      observedRate: percent(observed, evaluated),
      handoffRate: percent(handoff, total),
      averageAmount: moneyAverage(
        conversations.map((conversation) => conversation.credit_amount)
      ),
    };
  }, [conversations]);

  if (loading || isLoading) {
    return (
      <Box sx={{ display: "grid", placeItems: "center", minHeight: 420 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || isError) {
    return <Alert severity="error">No se pudieron cargar las metricas.</Alert>;
  }

  const summaryCards = [
    {
      label: "Conversaciones visibles",
      value: metrics.total,
      helper: `${stats?.conversations ?? metrics.total} en estadisticas`,
      icon: <ForumIcon />,
      color: "#0F766E",
    },
    {
      label: "Tasa preaprobada",
      value: `${metrics.preapprovedRate}%`,
      helper: `${metrics.preapproved} casos preaprobados`,
      icon: <CheckCircleIcon />,
      color: "#15803D",
    },
    {
      label: "Observados",
      value: metrics.observed,
      helper: `${metrics.observedRate}% de evaluados`,
      icon: <WarningIcon />,
      color: "#B45309",
    },
    {
      label: "Derivacion",
      value: `${metrics.handoffRate}%`,
      helper: `${metrics.handoff} con asesor`,
      icon: <SupportAgentIcon />,
      color: "#2563EB",
    },
  ];

  const statusRows = [
    { label: "Activas", value: metrics.active, total: metrics.total, color: "success" as const },
    { label: "Derivadas", value: metrics.handoff, total: metrics.total, color: "info" as const },
    { label: "Cerradas utiles", value: metrics.closed, total: metrics.total, color: "default" as const },
    { label: "Pendientes", value: metrics.pending, total: metrics.total, color: "warning" as const },
  ];

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4">Analitica</Typography>
        <Typography color="text.secondary">
          Indicadores de conversion y seguimiento calculados desde el dashboard.
        </Typography>
      </Box>

      <Grid container spacing={2.5}>
        {summaryCards.map((card) => (
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
                      color: card.color,
                      bgcolor: "#ECFEFF",
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
        <Grid size={{ xs: 12, md: 7 }}>
          <Card>
            <CardContent>
              <Stack spacing={2.5}>
                <Box>
                  <Typography variant="h6">Distribucion operativa</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Proporcion de estados sobre las conversaciones visibles.
                  </Typography>
                </Box>

                {statusRows.map((row) => (
                  <Box key={row.label}>
                    <Stack
                      direction="row"
                      sx={{ justifyContent: "space-between", mb: 1 }}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                        <Chip size="small" color={row.color} label={row.label} />
                        <Typography variant="body2" color="text.secondary">
                          {row.value} caso(s)
                        </Typography>
                      </Stack>
                      <Typography variant="body2" sx={{ fontWeight: 800 }}>
                        {percent(row.value, row.total)}%
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={percent(row.value, row.total)}
                      sx={{ height: 8, borderRadius: 1 }}
                    />
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent>
              <Stack spacing={2.5}>
                <Box>
                  <Typography variant="h6">Credito</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Lectura rapida de solicitudes con datos capturados.
                  </Typography>
                </Box>

                <Stack spacing={2}>
                  <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                    <Typography color="text.secondary">Monto promedio</Typography>
                    <Typography sx={{ fontWeight: 900 }}>
                      ${metrics.averageAmount.toLocaleString()}
                    </Typography>
                  </Stack>
                  <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                    <Typography color="text.secondary">Evaluadas</Typography>
                    <Typography sx={{ fontWeight: 900 }}>
                      {metrics.evaluated}
                    </Typography>
                  </Stack>
                  <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                    <Typography color="text.secondary">Pendientes</Typography>
                    <Typography sx={{ fontWeight: 900 }}>
                      {metrics.pending}
                    </Typography>
                  </Stack>
                </Stack>

                <Alert
                  icon={<QueryStatsIcon />}
                  severity={metrics.observed > metrics.preapproved ? "warning" : "success"}
                >
                  {metrics.observed > metrics.preapproved
                    ? "Hay mas casos observados que preaprobados. Revisa los motivos de rechazo y FAQs."
                    : "La relacion de preaprobados se mantiene por encima de observados."}
                </Alert>

                {metrics.total === 0 && (
                  <Alert icon={<ErrorIcon />} severity="info">
                    Todavia no hay conversaciones visibles para calcular metricas.
                  </Alert>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}
