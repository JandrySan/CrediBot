import { useRef, useState } from "react";

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import DeleteIcon from "@mui/icons-material/Delete";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import RefreshIcon from "@mui/icons-material/Refresh";

import { useDeleteFaq, useFaqs, useUploadFaqs } from "../hooks/useFaqs";

export function FaqAdminPage() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const faqsQuery = useFaqs();
  const uploadMutation = useUploadFaqs();
  const deleteMutation = useDeleteFaq();

  const handleFile = (file: File | null) => {
    if (!file) return;

    setFeedback(null);
    setError(null);

    uploadMutation.mutate(file, {
      onSuccess: (result) => {
        if (!result.success) {
          setError(result.message || "No se pudo cargar el archivo.");
          return;
        }

        setFeedback(
          `FAQs cargadas: ${result.created ?? 0}. Omitidas: ${result.skipped ?? 0}.`
        );
      },
      onError: () => {
        setError("No se pudo cargar el archivo. Revisa el formato e intenta de nuevo.");
      },
    });
  };

  const handleDelete = (faqId: number) => {
    setFeedback(null);
    setError(null);

    deleteMutation.mutate(faqId, {
      onSuccess: (result) => {
        if (result?.success) {
          setFeedback("FAQ eliminada.");
        } else {
          setError(result?.message || "No se pudo eliminar la FAQ.");
        }
      },
      onError: () => {
        setError("No se pudo eliminar la FAQ.");
      },
    });
  };

  return (
    <Box>
      <Stack
        direction={{ xs: "column", md: "row" }}
        spacing={2}
        sx={{ alignItems: { xs: "stretch", md: "center" }, justifyContent: "space-between", mb: 3 }}
      >
        <Box>
          <Typography variant="h4">FAQs</Typography>
          <Typography color="text.secondary">
            Base de conocimiento para requisitos, politicas y condiciones.
          </Typography>
        </Box>

        <Stack direction="row" spacing={1}>
          <input
            ref={inputRef}
            hidden
            type="file"
            accept=".json,.csv,application/json,text/csv"
            onChange={(event) => {
              handleFile(event.target.files?.[0] ?? null);
              event.target.value = "";
            }}
          />

          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => faqsQuery.refetch()}
          >
            Actualizar
          </Button>

          <Button
            variant="contained"
            startIcon={<UploadFileIcon />}
            disabled={uploadMutation.isPending}
            onClick={() => inputRef.current?.click()}
          >
            Cargar
          </Button>
        </Stack>
      </Stack>

      {feedback && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setFeedback(null)}>
          {feedback}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper} elevation={1}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Pregunta</TableCell>
              <TableCell>Respuesta</TableCell>
              <TableCell>Categoría</TableCell>
              <TableCell>Keywords</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {faqsQuery.isLoading && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}

            {!faqsQuery.isLoading && (faqsQuery.data?.length ?? 0) === 0 && (
              <TableRow>
                <TableCell colSpan={5}>
                  <Typography color="text.secondary">
                    No hay FAQs activas registradas.
                  </Typography>
                </TableCell>
              </TableRow>
            )}

            {faqsQuery.data?.map((faq) => (
              <TableRow key={faq.id} hover>
                <TableCell sx={{ width: "24%", fontWeight: 700 }}>
                  {faq.question}
                </TableCell>
                <TableCell sx={{ width: "36%" }}>{faq.answer}</TableCell>
                <TableCell>{faq.category || "General"}</TableCell>
                <TableCell>
                  <Stack direction="row" spacing={0.5} sx={{ flexWrap: "wrap", gap: 0.5 }}>
                    {faq.keywords.length === 0 && (
                      <Typography variant="body2" color="text.secondary">
                        Sin keywords
                      </Typography>
                    )}
                    {faq.keywords.map((keyword) => (
                      <Chip key={keyword} label={keyword} size="small" />
                    ))}
                  </Stack>
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    color="error"
                    disabled={deleteMutation.isPending}
                    onClick={() => handleDelete(faq.id)}
                    aria-label="Eliminar FAQ"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
