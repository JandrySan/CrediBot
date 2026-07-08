import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ConversationService } from "../services/conversation.service";

type ReplyPayload = {
  conversationId: number;
  message: string;
};

export function useReplyConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ conversationId, message }: ReplyPayload) =>
      ConversationService.replyConversation(conversationId, message),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation-messages"] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });
}