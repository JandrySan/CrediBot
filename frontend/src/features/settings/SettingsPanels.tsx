import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import ForumIcon from "@mui/icons-material/Forum";
import HelpIcon from "@mui/icons-material/Help";
import SettingsIcon from "@mui/icons-material/Settings";
import type { DashboardStats } from "../../services/dashboard.service";

export interface ConnectionItem {
  label: string;
  value: string;
  icon: ReactNode;
  ok: boolean;
  detail: string;
}

interface ChecklistItem {
  title: string;
  description: string;
  done: boolean;
}

export function ConnectionCards({ items }: { items: ConnectionItem[] }) {
  return (
    <Grid container spacing={2.5}>
      {items.map((item) => (
        <Grid size={{ xs: 12, lg: 4 }} key={item.label}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                  <Box sx={{ width: 42, height: 42, borderRadius: 2, bgcolor: "#CCFBF1", color: "#0F766E", display: "grid", placeItems: "center" }}>{item.icon}</Box>
                  <Chip size="small" color={item.ok ? "success" : "error"} label={item.detail} />
                </Stack>
                <Box>
                  <Typography sx={{ fontWeight: 800 }}>{item.label}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: "anywhere" }}>{item.value}</Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}

export function SettingsDetails({ checklist, stats }: { checklist: ChecklistItem[]; stats?: DashboardStats }) {
  const navigate = useNavigate();
  return (
    <Grid container spacing={2.5}>
      <Grid size={{ xs: 12, md: 7 }}>
        <Card>
          <CardContent>
            <Stack spacing={2.25}>
              <Box>
                <Typography variant="h6">Checklist operativo</Typography>
                <Typography variant="body2" color="text.secondary">Puntos mínimos para que WhatsApp, dashboard y audio funcionen.</Typography>
              </Box>
              {checklist.map((item) => (
                <Stack key={item.title} spacing={1}>
                  <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                    {item.done ? <CheckCircleIcon color="success" /> : <ErrorIcon color="error" />}
                    <Box>
                      <Typography sx={{ fontWeight: 800 }}>{item.title}</Typography>
                      <Typography variant="body2" color="text.secondary">{item.description}</Typography>
                    </Box>
                  </Stack>
                  <Divider />
                </Stack>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Grid>
      <Grid size={{ xs: 12, md: 5 }}>
        <Card>
          <CardContent>
            <Stack spacing={2.25}>
              <Box>
                <Typography variant="h6">Resumen del sistema</Typography>
                <Typography variant="body2" color="text.secondary">Lectura actual del backend.</Typography>
              </Box>
              {[
                ["Clientes", stats?.customers ?? "-"],
                ["Conversaciones", stats?.conversations ?? "-"],
                ["Activas", stats?.active_conversations ?? "-"],
              ].map(([label, value]) => (
                <Stack key={label} direction="row" sx={{ justifyContent: "space-between" }}>
                  <Typography color="text.secondary">{label}</Typography>
                  <Typography sx={{ fontWeight: 900 }}>{value}</Typography>
                </Stack>
              ))}
              <Divider />
              <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                <Button variant="outlined" startIcon={<ForumIcon />} onClick={() => navigate("/conversaciones")}>Conversaciones</Button>
                <Button variant="outlined" startIcon={<HelpIcon />} onClick={() => navigate("/faqs")}>FAQs</Button>
                <Button variant="outlined" startIcon={<SettingsIcon />} onClick={() => navigate("/analitica")}>Analítica</Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}
