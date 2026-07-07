import api from "../api/axios";
import type { Conversation } from "../types/conversation";

export const ConversationService = {

    async getAll(): Promise<Conversation[]> {

        const response = await api.get("/api/dashboard/conversations");

        return response.data;

    }

};