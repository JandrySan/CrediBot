import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  ConversationService,
  type ConversationResolution,
} from "../services/conversation.service";

type ClosePayload = {
  conversationId: number;
  resolution: ConversationResolution;
  note?: string;
};

export function useCloseConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ conversationId, resolution, note }: ClosePayload) =>
      ConversationService.closeConversation(conversationId, resolution, note ?? ""),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation-messages"] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });
}
