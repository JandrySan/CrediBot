import { useQuery } from "@tanstack/react-query";

import { ConversationService } from "../services/conversation.service";

export function useConversationMessages(conversationId: number | null) {
  return useQuery({
    queryKey: ["conversation-messages", conversationId],
    queryFn: () => ConversationService.getMessages(conversationId!),
    enabled: conversationId !== null,
    refetchInterval: 5000,
  });
}