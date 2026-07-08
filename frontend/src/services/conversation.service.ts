import api from "../api/axios";
import type { Conversation } from "../types/conversation";
import type { Message } from "../types/message";

export const ConversationService = {
  async getAll(): Promise<Conversation[]> {
    const response = await api.get("/api/dashboard/conversations");
    return response.data;
  },

  async getMessages(conversationId: number): Promise<Message[]> {
    const response = await api.get(
      `/api/dashboard/conversations/${conversationId}/messages`
    );

    return response.data;
  },
};