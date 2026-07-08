import {
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  Stack,
  Typography,
} from "@mui/material";

import type { Conversation } from "../../types/conversation";

type Props = {
  conversation: Conversation | null;
};

function InfoRow({ label, value }: { label: string; value: string | number }) {
  return (
    <Box>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography fontWeight={700}>{value}</Typography>
    </Box>
  );
}

export function ConversationInfoPanel({ conversation }: Props) {
  if (!conversation) {
    return (
      <Card elevation={1} sx={{ borderRadius: 3, height: 620 }}>
        <CardContent>
          <Typography color="text.secondary">
            Selecciona una conversación para ver la información del cliente.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card elevation={1} sx={{ borderRadius: 3, height: 620 }}>
      <CardContent>
        <Typography variant="h6" fontWeight={700} mb={2}>
          Información del cliente
        </Typography>

        <Stack spacing={2}>
          <InfoRow
            label="Cliente"
            value={conversation.full_name || "Sin nombre registrado"}
          />

          <InfoRow label="Teléfono" value={conversation.phone_number} />

          <Divider />

          <InfoRow
            label="Monto solicitado"
            value={
              conversation.credit_amount
                ? `$${conversation.credit_amount}`
                : "Pendiente"
            }
          />

          <InfoRow
            label="Plazo"
            value={
              conversation.term_months
                ? `${conversation.term_months} meses`
                : "Pendiente"
            }
          />

          <InfoRow
            label="Ingresos mensuales"
            value={
              conversation.monthly_income
                ? `$${conversation.monthly_income}`
                : "Pendiente"
            }
          />

          <Divider />

          <Box>
            <Typography variant="body2" color="text.secondary">
              Resultado
            </Typography>

            <Chip
              label={conversation.credit_result || "Pendiente"}
              color={
                conversation.credit_result === "PREAPROBADO"
                  ? "success"
                  : conversation.credit_result === "OBSERVADO"
                  ? "warning"
                  : "default"
              }
              sx={{ mt: 1 }}
            />
          </Box>

          <InfoRow
            label="Motivo"
            value={conversation.credit_reason || "Sin evaluación registrada"}
          />

          <Divider />

          <InfoRow label="Estado conversación" value={conversation.state} />
          <InfoRow label="Atención" value={conversation.status} />
        </Stack>
      </CardContent>
    </Card>
  );
}