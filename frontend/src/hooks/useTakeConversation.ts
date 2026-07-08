import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ConversationService } from "../services/conversation.service";

export function useTakeConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ConversationService.takeConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });
}