import { apiPost } from "./client";

export interface LlmExtractResponse {
  data: {
    budget: string;
    style: string[];
    deadline: string;
    colors: string[];
    item: string;
    constraints: string[];
  };
}

export async function extractRequirements(query: string, preferences: string[]): Promise<LlmExtractResponse> {
  return apiPost<LlmExtractResponse>("/api/llm/extract", { query, preferences });
}
