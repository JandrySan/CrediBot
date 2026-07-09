import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Stack,
  Typography,
} from "@mui/material";

import { useTakeConversation } from "../../hooks/useTakeConversation";
import { useCloseConversation } from "../../hooks/useCloseConversation";
import type { Conversation } from "../../types/conversation";
import type { ConversationResolution } from "../../services/conversation.service";

type Props = {
  conversation: Conversation | null;
};

function InfoRow({ label, value }: { label: string; value: string | number }) {
  return (
    <Box>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography sx={{ fontWeight: 700 }}>{value}</Typography>
    </Box>
  );
}

export function ConversationInfoPanel({ conversation }: Props) {
  const takeConversation = useTakeConversation();
  const closeConversation = useCloseConversation();

  const isHandoff = conversation?.status === "HANDOFF";
  const isClosed = conversation?.status === "CLOSED";
  const busy = takeConversation.isPending || closeConversation.isPending;

  const handleClose = (resolution: ConversationResolution) => {
    if (!conversation) return;

    closeConversation.mutate({
      conversationId: conversation.conversation_id,
      resolution,
    });
  };

  if (!conversation) {
    return (
      <Card elevation={1} sx={{ borderRadius: 3, height: 620 }}>
        <CardContent>
          <Typography color="text.secondary">
            Selecciona una conversacion para ver la informacion del cliente.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card elevation={1} sx={{ borderRadius: 3, height: 620, overflowY: "auto" }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
          Informacion del cliente
        </Typography>

        <Stack spacing={2}>
          <InfoRow
            label="Cliente"
            value={conversation.full_name || "Sin nombre registrado"}
          />

          <InfoRow label="Telefono" value={conversation.phone_number} />

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
            value={conversation.credit_reason || "Sin evaluacion registrada"}
          />

          <Divider />

          <InfoRow label="Estado conversacion" value={conversation.state} />
          <InfoRow label="Atencion" value={conversation.status} />

          <Divider />

          <Button
            variant="contained"
            color="primary"
            disabled={isHandoff || isClosed || busy}
            onClick={() => takeConversation.mutate(conversation.conversation_id)}
          >
            {isClosed
              ? "Conversacion cerrada"
              : isHandoff
                ? "Conversacion tomada"
                : "Tomar conversacion"}
          </Button>

          {isHandoff && (
            <Stack spacing={1}>
              <Typography variant="body2" color="text.secondary">
                Cuando termines con el cliente, cierra la conversacion:
              </Typography>

              <Button
                variant="outlined"
                color="success"
                disabled={busy}
                onClick={() => handleClose("APPROVED")}
              >
                Aprobar y cerrar
              </Button>

              <Button
                variant="outlined"
                color="error"
                disabled={busy}
                onClick={() => handleClose("DENIED")}
              >
                Negar y cerrar
              </Button>

              <Button
                variant="outlined"
                color="secondary"
                disabled={busy}
                onClick={() => handleClose("RESOLVED")}
              >
                Resuelta y cerrar
              </Button>
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
