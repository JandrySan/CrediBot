import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from "@mui/material";
import ErrorIcon from "@mui/icons-material/Error";
import QueryStatsIcon from "@mui/icons-material/QueryStats";

import type { ConversationMetrics } from "./metrics";
import { percent } from "./metrics";

export function AnalyticsDetails({ metrics }: { metrics: ConversationMetrics }) {
  const statusRows = [
    { label: "Activas", value: metrics.active, color: "success" as const },
    { label: "Derivadas", value: metrics.handoff, color: "info" as const },
    { label: "Cerradas", value: metrics.closed, color: "default" as const },
    { label: "Pendientes", value: metrics.pending, color: "warning" as const },
  ];

  return (
    <Grid container spacing={2.5}>
      <Grid size={{ xs: 12, md: 7 }}>
        <Card>
          <CardContent>
            <Stack spacing={2.5}>
              <Box>
                <Typography variant="h6">Distribución operativa</Typography>
                <Typography variant="body2" color="text.secondary">
                  Proporción de estados sobre las conversaciones visibles.
                </Typography>
              </Box>
              {statusRows.map((row) => {
                const rate = percent(row.value, metrics.total);
                return (
                  <Box key={row.label}>
                    <Stack direction="row" sx={{ justifyContent: "space-between", mb: 1 }}>
                      <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                        <Chip size="small" color={row.color} label={row.label} />
                        <Typography variant="body2" color="text.secondary">
                          {row.value} caso(s)
                        </Typography>
                      </Stack>
                      <Typography variant="body2" sx={{ fontWeight: 800 }}>{rate}%</Typography>
                    </Stack>
                    <LinearProgress variant="determinate" value={rate} sx={{ height: 8, borderRadius: 1 }} />
                  </Box>
                );
              })}
            </Stack>
          </CardContent>
        </Card>
      </Grid>
      <Grid size={{ xs: 12, md: 5 }}>
        <Card>
          <CardContent>
            <Stack spacing={2.5}>
              <Box>
                <Typography variant="h6">Crédito</Typography>
                <Typography variant="body2" color="text.secondary">
                  Lectura rápida de solicitudes con datos capturados.
                </Typography>
              </Box>
              {[
                ["Monto promedio", `$${metrics.averageAmount.toLocaleString()}`],
                ["Evaluadas", metrics.evaluated],
                ["Pendientes", metrics.pending],
              ].map(([label, value]) => (
                <Stack key={label} direction="row" sx={{ justifyContent: "space-between" }}>
                  <Typography color="text.secondary">{label}</Typography>
                  <Typography sx={{ fontWeight: 900 }}>{value}</Typography>
                </Stack>
              ))}
              <Alert
                icon={<QueryStatsIcon />}
                severity={metrics.observed > metrics.preapproved ? "warning" : "success"}
              >
                {metrics.observed > metrics.preapproved
                  ? "Hay más casos observados que preaprobados. Revisa sus motivos."
                  : "La relación de preaprobados se mantiene por encima de observados."}
              </Alert>
              {metrics.total === 0 && (
                <Alert icon={<ErrorIcon />} severity="info">
                  Todavía no hay conversaciones para calcular métricas.
                </Alert>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}
