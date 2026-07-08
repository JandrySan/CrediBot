import { useMemo, useState } from "react";

import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  List,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { useConversations } from "../../hooks/useConversations";
import { ConversationItem } from "./ConversationItem";
import type { Conversation } from "../../types/conversation";

type Props = {
  onSelect?: (conversation: Conversation) => void;
};

type FilterType = "ALL" | "ACTIVE" | "HANDOFF" | "PREAPPROVED" | "OBSERVED";

const filters: { label: string; value: FilterType }[] = [
  { label: "Todas", value: "ALL" },
  { label: "Activas", value: "ACTIVE" },
  { label: "Derivadas", value: "HANDOFF" },
  { label: "Preaprobadas", value: "PREAPPROVED" },
  { label: "Observadas", value: "OBSERVED" },
];

function normalize(value: string | null | undefined) {
  return (value ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

export function ConversationList({ onSelect }: Props) {
  const { data = [], isLoading, isError } = useConversations();

  const [search, setSearch] = useState("");
  const [selectedFilter, setSelectedFilter] = useState<FilterType>("ALL");

  const filteredConversations = useMemo(() => {
    const searchValue = normalize(search);

    console.log("BUSQUEDA:", search);
    console.log("FILTRO:", selectedFilter);
    console.log("DATA:", data);
    
    return data.filter((conversation) => {
      const name = normalize(conversation.full_name);
      const phone = normalize(conversation.phone_number);

      const matchesSearch =
        searchValue === "" ||
        name.includes(searchValue) ||
        phone.includes(searchValue);

      const matchesStatus =
        selectedFilter === "ALL" ||
        (selectedFilter === "ACTIVE" && conversation.status === "ACTIVE") ||
        (selectedFilter === "HANDOFF" && conversation.status === "HANDOFF") ||
        (selectedFilter === "PREAPPROVED" &&
          conversation.credit_result === "PREAPROBADO") ||
        (selectedFilter === "OBSERVED" &&
          conversation.credit_result === "OBSERVADO");

      return matchesSearch && matchesStatus;
    });
  }, [data, search, selectedFilter]);

  if (isLoading) {
    return (
      <Card elevation={1} sx={{ borderRadius: 3, height: 620 }}>
        <CardContent>
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return <Alert severity="error">No se pudieron cargar las conversaciones.</Alert>;
  }

  return (
    <Card elevation={1} sx={{ borderRadius: 3, height: 620, overflow: "hidden" }}>
      <CardContent>
        <Typography variant="h6" fontWeight={700} mb={2}>
          Conversaciones recientes
        </Typography>

        <TextField
          fullWidth
          size="small"
          placeholder="Buscar cliente o teléfono"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          sx={{ mb: 2 }}
        />

        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap mb={2}>
          {filters.map((item) => (
            <Chip
              key={item.value}
              label={item.label}
              clickable
              color={selectedFilter === item.value ? "primary" : "default"}
              variant={selectedFilter === item.value ? "filled" : "outlined"}
              onClick={() => setSelectedFilter(item.value)}
              size="small"
            />
          ))}
        </Stack>

        <List disablePadding sx={{ maxHeight: 440, overflowY: "auto" }}>
          {filteredConversations.map((conversation) => (
            <ConversationItem
              key={conversation.conversation_id}
              conversation={conversation}
              onClick={onSelect}
            />
          ))}
        </List>
      </CardContent>
    </Card>
  );
}