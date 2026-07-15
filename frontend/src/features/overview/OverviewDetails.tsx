import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from "@mui/material";
import HelpIcon from "@mui/icons-material/Help";
import SettingsIcon from "@mui/icons-material/Settings";
import WarningIcon from "@mui/icons-material/Warning";

import type { Conversation } from "../../types/conversation";

interface OverviewDetailsProps {
  conversations: Conversation[];
  preapprovedRate: number;
}

export function OverviewDetails({ conversations, preapprovedRate }: OverviewDetailsProps) {
  const navigate = useNavigate();
  return (
    <Grid container spacing={2.5}>
      <Grid size={{ xs: 12, lg: 7 }}>
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Box>
                <Typography variant="h6">Actividad reciente</Typography>
                <Typography variant="body2" color="text.secondary">
                  Últimas conversaciones visibles para seguimiento operativo.
                </Typography>
              </Box>
              {conversations.map((conversation) => (
                <Stack
                  key={conversation.conversation_id}
                  direction={{ xs: "column", sm: "row" }}
                  sx={{ alignItems: { xs: "flex-start", sm: "center" }, justifyContent: "space-between", gap: 1.5, py: 1.25, borderBottom: "1px solid #E2E8F0" }}
                >
                  <Box>
                    <Typography sx={{ fontWeight: 800 }}>
                      {conversation.full_name || conversation.phone_number}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">{conversation.phone_number}</Typography>
                  </Box>
                  <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                    <Chip size="small" label={conversation.status} />
                    <Chip
                      size="small"
                      color={conversation.credit_result === "PREAPROBADO" ? "success" : conversation.credit_result === "OBSERVADO" ? "warning" : "default"}
                      label={conversation.credit_result || "Pendiente"}
                    />
                  </Stack>
                </Stack>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Grid>
      <Grid size={{ xs: 12, lg: 5 }}>
        <Card>
          <CardContent>
            <Stack spacing={2.25}>
              <Box>
                <Typography variant="h6">Salud del flujo</Typography>
                <Typography variant="body2" color="text.secondary">Indicadores basados en las conversaciones actuales.</Typography>
              </Box>
              <Box>
                <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                  <Typography variant="body2">Preaprobación</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 800 }}>{preapprovedRate}%</Typography>
                </Stack>
                <LinearProgress variant="determinate" value={preapprovedRate} sx={{ mt: 1, height: 8, borderRadius: 1 }} />
              </Box>
              <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                <Button variant="outlined" startIcon={<HelpIcon />} onClick={() => navigate("/faqs")}>Revisar FAQs</Button>
                <Button variant="outlined" startIcon={<SettingsIcon />} onClick={() => navigate("/configuracion")}>Configuración</Button>
                <Button variant="outlined" color="warning" startIcon={<WarningIcon />} onClick={() => navigate("/analitica")}>Ver observados</Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}
