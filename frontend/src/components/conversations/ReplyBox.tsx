import { useState } from "react";
import axios from "axios";
import { Alert, Box, Button, TextField } from "@mui/material";

import type { Conversation } from "../../types/conversation";
import { useReplyConversation } from "../../hooks/useReplyConversation";

type Props = {
  conversation: Conversation | null;
};

export function ReplyBox({ conversation }: Props) {
  const [message, setMessage] = useState("");
  const [sendError, setSendError] = useState<string | null>(null);
  const replyMutation = useReplyConversation();

  const canReply =
    conversation?.status === "HANDOFF" ||
    conversation?.status === "MANOS LIBRES";
  const isClosed = conversation?.status === "CLOSED";

  const handleSend = () => {
    if (!conversation || !message.trim()) return;

    setSendError(null);

    replyMutation.mutate(
      {
        conversationId: conversation.conversation_id,
        message: message.trim(),
      },
      {
        onSuccess: (data) => {
          if (data?.success) {
            setMessage("");
            setSendError(null);
          } else {
            setSendError(
              data?.message ||
                "El mensaje se guardo en el panel, pero no llego a WhatsApp."
            );
          }
        },
        onError: (error) => {
          const backendMessage = axios.isAxiosError(error)
            ? error.response?.data?.message
            : "";

          setSendError(
            backendMessage ||
              "No se pudo enviar la respuesta. Revisa la conexion con el backend."
          );
        },
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
        flexDirection: "column",
        gap: 1,
      }}
    >
      {sendError && (
        <Alert severity="warning" onClose={() => setSendError(null)}>
          {sendError}
        </Alert>
      )}

      <Box sx={{ display: "flex", gap: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder={
            isClosed
              ? "Conversacion cerrada. Espera un nuevo mensaje para el bot."
              : canReply
                ? "Escribe una respuesta como asesor..."
                : "Toma la conversacion para responder"
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
    </Box>
  );
}
