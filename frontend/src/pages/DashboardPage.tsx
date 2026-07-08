import { useState } from "react";

import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Stack,
  Typography,
} from "@mui/material";

import PeopleIcon from "@mui/icons-material/People";
import ForumIcon from "@mui/icons-material/Forum";
import BoltIcon from "@mui/icons-material/Bolt";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningIcon from "@mui/icons-material/Warning";

import { ConversationList } from "../components/conversations/ConversationList";
import { ConversationChat } from "../components/conversations/ConversationChat";
import { ConversationInfoPanel } from "../components/conversations/ConversationInfoPanel";
import { useDashboard } from "../hooks/useDashboard";
import { useDashboardSocket } from "../hooks/useDashboardSocket";

import type { Conversation } from "../types/conversation";

export function DashboardPage() {
  useDashboardSocket();

  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);

  const { stats, loading, error } = useDashboard();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="70vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">No se pudo conectar con el backend.</Alert>;
  }

  const cards = [
    { title: "Clientes", value: stats?.customers ?? 0, icon: <PeopleIcon />, helper: "Registrados" },
    { title: "Conversaciones", value: stats?.conversations ?? 0, icon: <ForumIcon />, helper: "Totales" },
    { title: "Activas", value: stats?.active_conversations ?? 0, icon: <BoltIcon />, helper: "Bot activo" },
    { title: "Derivadas", value: stats?.handoff_conversations ?? 0, icon: <SupportAgentIcon />, helper: "Asesor humano" },
    { title: "Preaprobados", value: stats?.preapproved ?? 0, icon: <CheckCircleIcon />, helper: "Créditos viables" },
    { title: "Observados", value: stats?.observed ?? 0, icon: <WarningIcon />, helper: "Requieren revisión" },
  ];

  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h4">Panel operativo</Typography>
        <Typography color="text.secondary">
          Supervisión en tiempo real de WhatsApp, IA y precalificaciones.
        </Typography>
      </Box>

      <Grid container spacing={2.5}>
        {cards.map((card) => (
          <Grid item xs={12} sm={6} md={4} lg={2} key={card.title}>
            <Card sx={{ height: 132 }}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" fontWeight={700}>
                      {card.title}
                    </Typography>
                    <Typography variant="h3" fontWeight={900}>
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
                      borderRadius: 3,
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

      <Box
        sx={{
          display: "flex",
          gap: 3,
          mt: 3,
          alignItems: "stretch",
        }}
      >
        <Box sx={{ width: "33%", minWidth: 390 }}>
          <ConversationList onSelect={setSelectedConversation} />
        </Box>

        <Box sx={{ flex: 1, display: "flex", gap: 3 }}>
          <Box sx={{ flex: 2 }}>
            <ConversationChat conversation={selectedConversation} />
          </Box>

          <Box sx={{ width: 330 }}>
            <ConversationInfoPanel conversation={selectedConversation} />
          </Box>
        </Box>
      </Box>
    </Box>
  );
}