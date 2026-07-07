import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  List,
  Typography,
} from "@mui/material";

import { useConversations } from "../../hooks/useConversations";
import { ConversationItem } from "./ConversationItem";

export function ConversationList() {
  const { data, isLoading, isError } = useConversations();

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return <Alert severity="error">No se pudieron cargar las conversaciones.</Alert>;
  }

  return (
    <Card elevation={1} sx={{ borderRadius: 3, mt: 4 }}>
      <CardContent>
        <Typography variant="h6" fontWeight={700} mb={2}>
          Conversaciones recientes
        </Typography>

        <List disablePadding>
          {data?.map((conversation) => (
            <ConversationItem
              key={conversation.conversation_id}
              conversation={conversation}
            />
          ))}
        </List>
      </CardContent>
    </Card>
  );
}