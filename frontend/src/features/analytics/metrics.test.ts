import { describe, expect, it } from "vitest";
import type { Conversation } from "../../types/conversation";
import { calculateConversationMetrics, percent } from "./metrics";

function conversation(
  overrides: Partial<Conversation> = {}
): Conversation {
  return {
    conversation_id: 1,
    customer_id: 1,
    phone_number: "+593000000000",
    national_id: null,
    full_name: null,
    state: "GREETING",
    status: "ACTIVE",
    conversation_result: null,
    credit_amount: null,
    term_months: null,
    monthly_income: null,
    credit_result: null,
    credit_reason: null,
    created_at: "2026-07-15T00:00:00Z",
    ...overrides,
  };
}

describe("conversation metrics", () => {
  it("returns safe percentages for empty collections", () => {
    expect(percent(1, 0)).toBe(0);
    expect(calculateConversationMetrics([]).preapprovedRate).toBe(0);
  });

  it("summarizes statuses, results and average requested amount", () => {
    const metrics = calculateConversationMetrics([
      conversation({ credit_result: "PREAPROBADO", credit_amount: 1000 }),
      conversation({ conversation_id: 2, status: "HANDOFF", credit_result: "OBSERVADO", credit_amount: 2000 }),
      conversation({ conversation_id: 3, status: "CLOSED" }),
    ]);

    expect(metrics).toMatchObject({
      total: 3,
      active: 1,
      handoff: 1,
      closed: 1,
      preapproved: 1,
      observed: 1,
      pending: 1,
      evaluated: 2,
      preapprovedRate: 50,
      handoffRate: 33,
      averageAmount: 1500,
    });
  });
});
