const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface QueryAnalysisResult {
  original_query: string;
  domain: string;
  task: string;
  data_type: string;
  keywords: string[];
  entities: { text: string; label: string }[];
  understanding_source: "llm" | "rule_based";
}

export interface DatasetMatch {
  id: number | string;
  name: string;
  domain: string;
  task: string;
  description: string;
  similarity: number;
  source: "catalog" | "kaggle";
}

export interface EvaluatedDataset {
  dataset: DatasetMatch;
  score: number;
  explanation: string;
}

export interface DiscoverResponse {
  understanding: QueryAnalysisResult;
  recommendations: EvaluatedDataset[];
}

export class ApiError extends Error {}

export async function discover(query: string, k = 5): Promise<DiscoverResponse> {
  const params = new URLSearchParams({ query, k: String(k) });
  const response = await fetch(`${API_BASE_URL}/discover?${params.toString()}`, {
    method: "POST",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.detail ? JSON.stringify(body.detail) : `Request failed (${response.status})`);
  }

  return response.json();
}
