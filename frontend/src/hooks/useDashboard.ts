import { useEffect, useState } from "react";
import { DashboardService } from "../services/dashboard.service";
import type { DashboardStats } from "../services/dashboard.service";


export function useDashboard() {

    const [stats, setStats] = useState<DashboardStats | null>(null);

    const [loading, setLoading] = useState(true);

    const [error, setError] = useState("");

    useEffect(() => {

        DashboardService.getStats()

            .then((response) => {

                setStats(response);

            })

            .catch(() => {

                setError("No se pudo conectar con el backend.");

            })

            .finally(() => {

                setLoading(false);

            });

    }, []);

    return {

        stats,

        loading,

        error,

    };

}