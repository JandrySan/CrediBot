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
};

function getResultColor(result: string | null) {
  if (result === "PREAPROBADO") return "success";
  if (result === "OBSERVADO") return "warning";
  if (result === "RECHAZADO") return "error";
  return "default";
}

export function ConversationItem({ conversation }: Props) {
  const name = conversation.full_name || conversation.phone_number;
  const initials = name.substring(0, 2).toUpperCase();

  return (
    <ListItemButton
      sx={{
        borderRadius: 3,
        mb: 1,
        border: "1px solid #e5e7eb",
        backgroundColor: "white",
      }}
    >
      <Avatar sx={{ bgcolor: "#128C7E", mr: 2 }}>{initials}</Avatar>

      <Box sx={{ flex: 1 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography fontWeight={700}>{name}</Typography>

          <Chip
            size="small"
            label={conversation.status}
            color={conversation.status === "HANDOFF" ? "warning" : "success"}
          />
        </Stack>

        <Typography variant="body2" color="text.secondary">
          Estado: {conversation.state}
        </Typography>

        <Stack direction="row" spacing={1} mt={1}>
          <Chip
            size="small"
            label={conversation.credit_result || "Pendiente"}
            color={getResultColor(conversation.credit_result) as any}
            variant="outlined"
          />

          {conversation.credit_amount && (
            <Chip
              size="small"
              label={`$${conversation.credit_amount}`}
              variant="outlined"
            />
          )}
        </Stack>
      </Box>
    </ListItemButton>
  );
}