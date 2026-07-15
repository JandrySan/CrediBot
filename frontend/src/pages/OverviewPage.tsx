import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Box, Button, CircularProgress, Grid, Stack, Typography } from "@mui/material";
import AssessmentIcon from "@mui/icons-material/Assessment";
import ChatIcon from "@mui/icons-material/Chat";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ForumIcon from "@mui/icons-material/Forum";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";

import { SummaryMetricCard } from "../components/dashboard/SummaryMetricCard";
import { percent } from "../features/analytics/metrics";
import { OverviewDetails } from "../features/overview/OverviewDetails";
import { useConversations } from "../hooks/useConversations";
import { useDashboard } from "../hooks/useDashboard";

export function OverviewPage() {
  const navigate = useNavigate();
  const { stats, loading, error } = useDashboard();
  const { data: conversations = [], isLoading } = useConversations();
  const recentConversations = useMemo(() => conversations.slice(0, 5), [conversations]);
  const preapprovedRate = percent(
    stats?.preapproved ?? 0,
    (stats?.preapproved ?? 0) + (stats?.observed ?? 0)
  );

  if (loading || isLoading) {
    return <Box sx={{ display: "grid", placeItems: "center", minHeight: 420 }}><CircularProgress /></Box>;
  }
  if (error) return <Alert severity="error">No se pudo conectar con el backend.</Alert>;

  const cards = [
    { label: "Conversaciones", value: stats?.conversations ?? 0, helper: "Visibles en dashboard", icon: <ForumIcon /> },
    { label: "Activas", value: stats?.active_conversations ?? 0, helper: "Atendidas por bot", icon: <ChatIcon /> },
    { label: "Derivadas", value: stats?.handoff_conversations ?? 0, helper: "Esperando asesor", icon: <SupportAgentIcon /> },
    { label: "Preaprobados", value: stats?.preapproved ?? 0, helper: `${preapprovedRate}% de casos evaluados`, icon: <CheckCircleIcon /> },
  ];

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: "column", md: "row" }} sx={{ justifyContent: "space-between", gap: 2 }}>
        <Box>
          <Typography variant="h4">Panel operativo</Typography>
          <Typography color="text.secondary">Resumen rápido de atención, precalificaciones y estado del sistema.</Typography>
        </Box>
        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
          <Button variant="contained" startIcon={<ChatIcon />} onClick={() => navigate("/conversaciones")}>Ver conversaciones</Button>
          <Button variant="outlined" startIcon={<AssessmentIcon />} onClick={() => navigate("/analitica")}>Analítica</Button>
        </Stack>
      </Stack>
      <Grid container spacing={2.5}>
        {cards.map((card) => <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={card.label}><SummaryMetricCard {...card} /></Grid>)}
      </Grid>
      <OverviewDetails conversations={recentConversations} preapprovedRate={preapprovedRate} />
    </Stack>
  );
}
