import type { AgentLogEntry } from "@/types/agent";
import { apiGet } from "./client";

export async function fetchAgentLogs(): Promise<AgentLogEntry[]> {
  return apiGet<AgentLogEntry[]>("/api/agent/logs");
}
