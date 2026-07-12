import { useQuery } from "@tanstack/react-query";

import { ConversationService } from "../services/conversation.service";
import type { Conversation } from "../types/conversation";

function dedupeConversations(conversations: Conversation[]): Conversation[] {
  const seen = new Map<number, Conversation>();

  for (const conversation of conversations) {
    const existing = seen.get(conversation.conversation_id);

    if (!existing) {
      seen.set(conversation.conversation_id, conversation);
      continue;
    }

    if (!existing.credit_result && conversation.credit_result) {
      seen.set(conversation.conversation_id, conversation);
    }
  }

  return Array.from(seen.values());
}

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: ConversationService.getAll,
    select: dedupeConversations,
    refetchInterval: 5000,
  });
}
