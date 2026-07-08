import { useState } from "react";
import { Box, Button, TextField } from "@mui/material";

import type { Conversation } from "../../types/conversation";
import { useReplyConversation } from "../../hooks/useReplyConversation";

type Props = {
  conversation: Conversation | null;
};

export function ReplyBox({ conversation }: Props) {
  const [message, setMessage] = useState("");
  const replyMutation = useReplyConversation();

  const canReply =
    conversation?.status === "HANDOFF" ||
    conversation?.status === "MANOS LIBRES";

  const handleSend = () => {
    if (!conversation || !message.trim()) return;

    replyMutation.mutate(
      {
        conversationId: conversation.conversation_id,
        message: message.trim(),
      },
      {
        onSuccess: () => setMessage(""),
      }
    );
  };

  return (
    <Box
      sx={{
        p: 2,
        borderTop: "1px solid #ddd",
        backgroundColor: "white",
        display: "flex",
        gap: 1,
      }}
    >
      <TextField
        fullWidth
        size="small"
        placeholder={
          canReply
            ? "Escribe una respuesta como asesor..."
            : "Toma la conversación para responder"
        }
        value={message}
        disabled={!canReply || replyMutation.isPending}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            handleSend();
          }
        }}
      />

      <Button
        variant="contained"
        disabled={!canReply || !message.trim() || replyMutation.isPending}
        onClick={handleSend}
      >
        Enviar
      </Button>
    </Box>
  );
}