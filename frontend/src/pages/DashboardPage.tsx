import { useState } from "react";

import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Typography,
} from "@mui/material";

import { ConversationList } from "../components/conversations/ConversationList";
import { ConversationChat } from "../components/conversations/ConversationChat";
import { useDashboard } from "../hooks/useDashboard";

import { ConversationInfoPanel } from "../components/conversations/ConversationInfoPanel";

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
    { title: "Clientes", value: stats?.customers ?? 0 },
    { title: "Conversaciones", value: stats?.conversations ?? 0 },
    { title: "Activas", value: stats?.active_conversations ?? 0 },
    { title: "Derivadas", value: stats?.handoff_conversations ?? 0 },
    { title: "Preaprobados", value: stats?.preapproved ?? 0 },
    { title: "Observados", value: stats?.observed ?? 0 },
  ];

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" mb={3}>
        Panel
      </Typography>

      <Grid container spacing={3}>
        {cards.map((card) => (
          <Grid item xs={12} sm={6} md={4} lg={2} key={card.title}>
            <Card elevation={1} sx={{ borderRadius: 3 }}>
              <CardContent>
                <Typography color="text.secondary" fontWeight={500}>
                  {card.title}
                </Typography>

                <Typography variant="h3" fontWeight={700}>
                  {card.value}
                </Typography>
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
        <Box sx={{ width: "34%", minWidth: 360 }}>
          <ConversationList onSelect={setSelectedConversation} />
        </Box>

        <Box sx={{ flex: 1, display: "flex", gap: 3 }}>
          <Box sx={{ flex: 2 }}>
            <ConversationChat conversation={selectedConversation} />
          </Box>

          <Box sx={{ width: 320 }}>
            <ConversationInfoPanel conversation={selectedConversation} />
          </Box>
        </Box>
      </Box>
    </Box>
  );
}