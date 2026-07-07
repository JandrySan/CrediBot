import { useQuery } from "@tanstack/react-query";

import { ConversationService } from "../services/conversation.service";

export function useConversations() {

    return useQuery({

        queryKey: ["conversations"],

        queryFn: ConversationService.getAll,

        refetchInterval: 5000,

    });

}