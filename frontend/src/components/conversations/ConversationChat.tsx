import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Typography,
} from "@mui/material";

import type { Conversation } from "../../types/conversation";
import { useConversationMessages } from "../../hooks/useConversationMessages";
import { ReplyBox } from "./ReplyBox";

type Props = {
  conversation: Conversation | null;
};

export function ConversationChat({ conversation }: Props) {
  const conversationId = conversation?.conversation_id ?? null;

  const { data, isLoading } = useConversationMessages(conversationId);

  if (!conversation) {
    return (
      <Card elevation={1} sx={{ borderRadius: 3, height: 620 }}>
        <CardContent>
          <Typography color="text.secondary">
            Selecciona una conversación para ver el chat.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card elevation={1} sx={{ borderRadius: 3, height: 620 }}>
        <CardContent>
          <Box display="flex" justifyContent="center" py={6}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      elevation={1}
      sx={{
        borderRadius: 3,
        height: 620,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          p: 2,
          borderBottom: "1px solid #e5e7eb",
          backgroundColor: "#075E54",
          color: "white",
        }}
      >
        <Typography fontWeight={700}>
          {conversation.full_name || conversation.phone_number}
        </Typography>

        <Typography variant="body2" sx={{ opacity: 0.85 }}>
          {conversation.status} · {conversation.state}
        </Typography>
      </Box>

      <CardContent
        sx={{
          flex: 1,
          overflowY: "auto",
          backgroundColor: "#e5ddd5",
          display: "flex",
          flexDirection: "column",
          gap: 1.5,
        }}
      >
        {data?.map((message) => {
          const isInbound = message.direction === "INBOUND";

          return (
            <Box
              key={message.id}
              sx={{
                display: "flex",
                justifyContent: isInbound ? "flex-start" : "flex-end",
              }}
            >
              <Box
                sx={{
                  maxWidth: "75%",
                  backgroundColor: isInbound ? "white" : "#dcf8c6",
                  px: 2,
                  py: 1,
                  borderRadius: 2,
                  boxShadow: "0 1px 1px rgba(0,0,0,0.15)",
                }}
              >
                <Typography variant="body2">{message.content}</Typography>

                {message.type === "AUDIO" && (
                  <Chip size="small" label="Audio" sx={{ mt: 1 }} />
                )}
              </Box>
            </Box>
          );
        })}
      </CardContent>

      <ReplyBox conversation={conversation} />
    </Card>
  );
}