import type { Conversation } from "../../types/conversation";

export function percent(value: number, total: number) {
  return total ? Math.round((value / total) * 100) : 0;
}

function countWhere(
  conversations: Conversation[],
  predicate: (conversation: Conversation) => boolean
) {
  return conversations.filter(predicate).length;
}

function moneyAverage(values: Array<number | null>) {
  const cleanValues = values.filter((value): value is number => value !== null);
  if (!cleanValues.length) return 0;
  return Math.round(
    cleanValues.reduce((total, value) => total + value, 0) / cleanValues.length
  );
}

export function calculateConversationMetrics(conversations: Conversation[]) {
  const total = conversations.length;
  const active = countWhere(conversations, ({ status }) => status === "ACTIVE");
  const handoff = countWhere(
    conversations,
    ({ status }) => status === "HANDOFF" || status === "MANOS LIBRES"
  );
  const closed = countWhere(conversations, ({ status }) => status === "CLOSED");
  const preapproved = countWhere(
    conversations,
    ({ credit_result }) => credit_result === "PREAPROBADO"
  );
  const observed = countWhere(
    conversations,
    ({ credit_result }) => credit_result === "OBSERVADO"
  );
  const pending = countWhere(conversations, ({ credit_result }) => !credit_result);
  const evaluated = preapproved + observed;

  return {
    total,
    active,
    handoff,
    closed,
    preapproved,
    observed,
    pending,
    evaluated,
    preapprovedRate: percent(preapproved, evaluated),
    observedRate: percent(observed, evaluated),
    handoffRate: percent(handoff, total),
    averageAmount: moneyAverage(
      conversations.map(({ credit_amount }) => credit_amount)
    ),
  };
}

export type ConversationMetrics = ReturnType<typeof calculateConversationMetrics>;
