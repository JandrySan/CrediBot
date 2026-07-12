export interface Message {
  id: number;
  direction: "INBOUND" | "OUTBOUND";
  type: "TEXT" | "AUDIO";
  content: string;
  created_at: string;
  tool_calls?: ToolCallSummary[];
}

export interface ToolCallSummary {
  tool_name: string;
  success?: boolean;
  arguments?: Record<string, unknown> | string;
  result?: unknown;
  error?: string;
}
