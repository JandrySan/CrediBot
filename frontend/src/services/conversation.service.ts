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
  async takeConversation(conversationId: number) {
    const response = await api.post(
      `/api/dashboard/conversations/${conversationId}/take`
    );

    return response.data;
  },

  async replyConversation(conversationId: number, message: string) {
    const formData = new FormData();
    formData.append("message", message);

    const response = await api.post(
      `/api/dashboard/conversations/${conversationId}/reply`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

    return response.data;
  },
};