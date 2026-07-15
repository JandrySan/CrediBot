import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { WS_BASE_URL } from "../config/api";
import { AuthStorage } from "../services/auth.storage";

export function useDashboardSocket() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = AuthStorage.getToken();
    const query = token ? `?token=${encodeURIComponent(token)}` : "";
    const socket = new WebSocket(`${WS_BASE_URL}/ws/dashboard${query}`);

    socket.onmessage = () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["conversation-messages"] });
    };

    return () => {
      socket.close();
    };
  }, [queryClient]);
}
