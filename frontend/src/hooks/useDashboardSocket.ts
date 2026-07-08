import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

export function useDashboardSocket() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const socket = new WebSocket("ws://127.0.0.1:8000/ws/dashboard");

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