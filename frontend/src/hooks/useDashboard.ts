import { useQuery } from "@tanstack/react-query";
import { DashboardService } from "../services/dashboard.service";

export function useDashboard() {
  const statsQuery = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: DashboardService.getStats,
    refetchInterval: 5000,
  });

  return {
    stats: statsQuery.data,
    loading: statsQuery.isLoading,
    error: statsQuery.isError,
  };
}