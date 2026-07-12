import {
  Avatar,
  Box,
  Chip,
  ListItemButton,
  Stack,
  Typography,
} from "@mui/material";
import type { ChipProps } from "@mui/material";

import type { Conversation } from "../../types/conversation";

type Props = {
  conversation: Conversation;
  selected?: boolean;
  onClick?: (conversation: Conversation) => void;
};

function getResultColor(result: string | null): ChipProps["color"] {
  if (result === "PREAPROBADO") return "success";
  if (result === "OBSERVADO") return "warning";
  if (result === "RECHAZADO") return "error";
  return "default";
}

function getStatusLabel(status: string) {
  if (status === "HANDOFF" || status === "MANOS LIBRES") return "Asesor";
  if (status === "CLOSED") return "Cerrada";
  if (status === "ACTIVE") return "Bot";
  return status;
}

export function ConversationItem({
  conversation,
  selected = false,
  onClick,
}: Props) {
  const name = conversation.full_name || conversation.phone_number;
  const initials = name.substring(0, 2).toUpperCase();

  return (
    <ListItemButton
      selected={selected}
      onClick={() => onClick?.(conversation)}
      sx={{
        borderRadius: 4,
        mb: 1.2,
        p: 1.5,
        border: selected ? "2px solid #0F766E" : "1px solid #E2E8F0",
        backgroundColor: selected ? "#F0FDFA" : "white",
        transition: "0.2s ease",
        "&:hover": {
          borderColor: "#0F766E",
          transform: "translateY(-1px)",
          boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
        },
        "&.Mui-selected": {
          backgroundColor: "#F0FDFA",
          "&:hover": {
            backgroundColor: "#CCFBF1",
          },
        },
      }}
    >
      <Avatar
        sx={{
          bgcolor:
            conversation.status === "HANDOFF" ||
            conversation.status === "MANOS LIBRES"
              ? "#F97316"
              : conversation.status === "CLOSED"
                ? "#64748B"
              : "#0F766E",
          mr: 1.5,
          fontWeight: 900,
        }}
      >
        {initials}
      </Avatar>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Stack
          direction="row"
          sx={{ justifyContent: "space-between", alignItems: "center" }}
        >
          <Typography noWrap sx={{ fontWeight: 800 }}>
            {name}
          </Typography>

          <Chip
            size="small"
            label={getStatusLabel(conversation.status)}
            color={
              conversation.status === "HANDOFF" ||
              conversation.status === "MANOS LIBRES"
                ? "warning"
                : conversation.status === "CLOSED"
                  ? "default"
                : "success"
            }
          />
        </Stack>

        <Typography variant="body2" color="text.secondary" noWrap>
          {conversation.state.replaceAll("_", " ")}
        </Typography>

        <Stack
          direction="row"
          spacing={1}
          sx={{ mt: 1, alignItems: "center" }}
        >
          <Chip
            size="small"
            label={conversation.credit_result || "Pendiente"}
            color={getResultColor(conversation.credit_result)}
            variant="outlined"
          />

          {conversation.credit_amount && (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 700 }}
            >
              ${conversation.credit_amount} · {conversation.term_months || "-"} meses
            </Typography>
          )}
        </Stack>
      </Box>
    </ListItemButton>
  );
}
