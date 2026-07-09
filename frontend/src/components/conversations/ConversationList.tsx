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

import SearchIcon from "@mui/icons-material/Search";

import { useConversations } from "../../hooks/useConversations";
import { ConversationItem } from "./ConversationItem";
import type { Conversation } from "../../types/conversation";

type Props = {
  onSelect?: (conversation: Conversation) => void;
};

type FilterType = "ALL" | "ACTIVE" | "HANDOFF" | "PREAPPROVED" | "OBSERVED";

const filters: { label: string; value: FilterType }[] = [
  { label: "Todas", value: "ALL" },
  { label: "Bot", value: "ACTIVE" },
  { label: "Asesor", value: "HANDOFF" },
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

    return data.filter((conversation) => {
      const name = normalize(conversation.full_name);
      const phone = normalize(conversation.phone_number);

      const matchesSearch =
        searchValue === "" ||
        name.includes(searchValue) ||
        phone.includes(searchValue);

      const matchesFilter =
        selectedFilter === "ALL" ||
        (selectedFilter === "ACTIVE" && conversation.status === "ACTIVE") ||
        (selectedFilter === "HANDOFF" &&
          (conversation.status === "HANDOFF" ||
            conversation.status === "MANOS LIBRES")) ||
        (selectedFilter === "PREAPPROVED" &&
          conversation.credit_result === "PREAPROBADO") ||
        (selectedFilter === "OBSERVED" &&
          conversation.credit_result === "OBSERVADO");

      return matchesSearch && matchesFilter;
    });
  }, [data, search, selectedFilter]);

  if (isLoading) {
    return (
      <Card sx={{ borderRadius: 4, height: 620 }}>
        <CardContent>
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
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
    <Card sx={{ borderRadius: 4, height: 620, overflow: "hidden" }}>
      <CardContent sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
        <Stack direction="row" sx={{ justifyContent: "space-between", mb: 2 }}>
          <Box>
            <Typography variant="h6">Conversaciones</Typography>
            <Typography variant="body2" color="text.secondary">
              {filteredConversations.length} resultado(s)
            </Typography>
          </Box>
        </Stack>

        <TextField
          fullWidth
          size="small"
          placeholder="Buscar cliente o teléfono"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          slotProps={{
            input: {
              startAdornment: <SearchIcon sx={{ color: "#94A3B8", mr: 1 }} />,
            },
          }}
          sx={{ mb: 2 }}
        />

        <Stack
          direction="row"
          spacing={1}
          useFlexGap
          sx={{ mb: 2, flexWrap: "wrap" }}
        >
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

        <List disablePadding sx={{ flex: 1, overflowY: "auto", pr: 1 }}>
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