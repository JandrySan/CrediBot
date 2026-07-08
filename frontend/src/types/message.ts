export interface Message {
  id: number;
  direction: "INBOUND" | "OUTBOUND";
  type: "TEXT" | "AUDIO";
  content: string;
  created_at: string;
}