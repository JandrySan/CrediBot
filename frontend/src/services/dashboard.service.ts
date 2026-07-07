import api from "../api/axios";

export interface DashboardStats {
    customers: number;
    conversations: number;
    active_conversations: number;
    handoff_conversations: number;
    preapproved: number;
    observed: number;
}

export const DashboardService = {

    async getStats(): Promise<DashboardStats> {

        const response = await api.get("/api/dashboard/stats");

        return response.data;

    },

};