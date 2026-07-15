import type { ReactNode } from "react";
import { Box, Card, CardContent, Stack, Typography } from "@mui/material";

interface SummaryMetricCardProps {
  label: string;
  value: ReactNode;
  helper: string;
  icon: ReactNode;
  color?: string;
}

export function SummaryMetricCard({
  label,
  value,
  helper,
  icon,
  color = "#0F766E",
}: SummaryMetricCardProps) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Stack direction="row" sx={{ justifyContent: "space-between" }}>
          <Box>
            <Typography color="text.secondary" sx={{ fontWeight: 700 }}>
              {label}
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 900 }}>
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {helper}
            </Typography>
          </Box>
          <Box
            sx={{
              width: 42,
              height: 42,
              borderRadius: 2,
              color,
              bgcolor: "#ECFEFF",
              display: "grid",
              placeItems: "center",
            }}
          >
            {icon}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}
