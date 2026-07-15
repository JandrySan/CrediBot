import { useMemo } from "react";
import { Alert, Box, CircularProgress, Grid, Stack, Typography } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ForumIcon from "@mui/icons-material/Forum";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import WarningIcon from "@mui/icons-material/Warning";

import { SummaryMetricCard } from "../components/dashboard/SummaryMetricCard";
import { AnalyticsDetails } from "../features/analytics/AnalyticsDetails";
import { calculateConversationMetrics } from "../features/analytics/metrics";
import { useConversations } from "../hooks/useConversations";
import { useDashboard } from "../hooks/useDashboard";

export function AnalyticsPage() {
  const { stats, loading, error } = useDashboard();
  const { data: conversations = [], isLoading, isError } = useConversations();
  const metrics = useMemo(
    () => calculateConversationMetrics(conversations),
    [conversations]
  );

  if (loading || isLoading) {
    return <Box sx={{ display: "grid", placeItems: "center", minHeight: 420 }}><CircularProgress /></Box>;
  }
  if (error || isError) {
    return <Alert severity="error">No se pudieron cargar las métricas.</Alert>;
  }

  const cards = [
    { label: "Conversaciones visibles", value: metrics.total, helper: `${stats?.conversations ?? metrics.total} en estadísticas`, icon: <ForumIcon />, color: "#0F766E" },
    { label: "Tasa preaprobada", value: `${metrics.preapprovedRate}%`, helper: `${metrics.preapproved} casos preaprobados`, icon: <CheckCircleIcon />, color: "#15803D" },
    { label: "Observados", value: metrics.observed, helper: `${metrics.observedRate}% de evaluados`, icon: <WarningIcon />, color: "#B45309" },
    { label: "Derivación", value: `${metrics.handoffRate}%`, helper: `${metrics.handoff} con asesor`, icon: <SupportAgentIcon />, color: "#2563EB" },
  ];

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4">Analítica</Typography>
        <Typography color="text.secondary">
          Indicadores de conversión y seguimiento calculados desde el dashboard.
        </Typography>
      </Box>
      <Grid container spacing={2.5}>
        {cards.map((card) => (
          <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={card.label}>
            <SummaryMetricCard {...card} />
          </Grid>
        ))}
      </Grid>
      <AnalyticsDetails metrics={metrics} />
    </Stack>
  );
}
