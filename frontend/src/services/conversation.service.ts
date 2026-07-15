import api from "../api/axios";
import type { Conversation } from "../types/conversation";
import type { Message } from "../types/message";

export type ConversationResolution = "APPROVED" | "DENIED" | "RESOLVED";

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
  async takeConversation(conversationId: number) {
    const response = await api.post(
      `/api/dashboard/conversations/${conversationId}/take`
    );

    return response.data;
  },

  async replyConversation(conversationId: number, message: string) {
    const response = await api.post(
      `/api/dashboard/conversations/${conversationId}/reply`,
      { message }
    );

    return response.data;
  },

  async closeConversation(
    conversationId: number,
    resolution: ConversationResolution,
    note = ""
  ) {
    const response = await api.post(
      `/api/dashboard/conversations/${conversationId}/close`,
      { resolution, note }
    );

    return response.data;
  },
};
