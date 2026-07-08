import {
  Avatar,
  Box,
  Chip,
  ListItemButton,
  Stack,
  Typography,
} from "@mui/material";

import type { Conversation } from "../../types/conversation";

type Props = {
  conversation: Conversation;
  onClick?: (conversation: Conversation) => void;
};

function getResultColor(result: string | null) {
  if (result === "PREAPROBADO") return "success";
  if (result === "OBSERVADO") return "warning";
  if (result === "RECHAZADO") return "error";
  return "default";
}

function getStatusLabel(status: string) {
  if (status === "HANDOFF" || status === "MANOS LIBRES") return "Asesor";
  if (status === "ACTIVE") return "Bot";
  return status;
}

export function ConversationItem({ conversation, onClick }: Props) {
  const name = conversation.full_name || conversation.phone_number;
  const initials = name.substring(0, 2).toUpperCase();

  return (
    <ListItemButton
      onClick={() => onClick?.(conversation)}
      sx={{
        borderRadius: 4,
        mb: 1.2,
        p: 1.5,
        border: "1px solid #E2E8F0",
        backgroundColor: "white",
        transition: "0.2s ease",
        "&:hover": {
          borderColor: "#0F766E",
          transform: "translateY(-1px)",
          boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
        },
      }}
    >
      <Avatar
        sx={{
          bgcolor:
            conversation.status === "HANDOFF" ||
            conversation.status === "MANOS LIBRES"
              ? "#F97316"
              : "#0F766E",
          mr: 1.5,
          fontWeight: 900,
        }}
      >
        {initials}
      </Avatar>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography fontWeight={800} noWrap>
            {name}
          </Typography>

          <Chip
            size="small"
            label={getStatusLabel(conversation.status)}
            color={
              conversation.status === "HANDOFF" ||
              conversation.status === "MANOS LIBRES"
                ? "warning"
                : "success"
            }
          />
        </Stack>

        <Typography variant="body2" color="text.secondary" noWrap>
          {conversation.state.replaceAll("_", " ")}
        </Typography>

        <Stack direction="row" spacing={1} mt={1} alignItems="center">
          <Chip
            size="small"
            label={conversation.credit_result || "Pendiente"}
            color={getResultColor(conversation.credit_result) as any}
            variant="outlined"
          />

          {conversation.credit_amount && (
            <Typography variant="caption" color="text.secondary" fontWeight={700}>
              ${conversation.credit_amount} · {conversation.term_months || "-"} meses
            </Typography>
          )}
        </Stack>
      </Box>
    </ListItemButton>
  );
}