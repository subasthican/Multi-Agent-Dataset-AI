const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const TOKEN_STORAGE_KEY = "data_nebula_token";

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
  source: "catalog" | "kaggle" | "openml" | "huggingface";
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

export interface RecommendationResponse {
  based_on_domain: string | null;
  based_on_task: string | null;
  search_count: number;
  recommendations: EvaluatedDataset[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  // Plans are admin-managed and dynamic now (see Plan below), not a fixed
  // "free" | "pro" union — an admin can create/rename/delete tiers.
  plan: string;
  is_admin: boolean;
  created_at: string;
}

export interface AdminUser extends User {
  search_count: number;
}

export interface AdminStats {
  total_users: number;
  pro_users: number;
  admin_users: number;
  total_searches: number;
  searches_via_llm: number;
  searches_via_rule_based: number;
  catalog_size: number;
}

export interface CatalogDataset {
  id: string;
  name: string;
  description: string;
  domain: string;
  task: string;
  created_at: string;
  updated_at: string;
}

export interface CatalogDatasetInput {
  name: string;
  description: string;
  domain: string;
  task: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Plan {
  id: string;
  name: string; // stable key stored on User.plan — not editable after creation
  display_name: string;
  price_label: string;
  period: string | null;
  description: string;
  features: string[];
  daily_search_limit: number | null; // null = unlimited
  created_at: string;
  updated_at: string;
}

export interface PlanInput {
  name: string;
  display_name: string;
  price_label: string;
  period?: string | null;
  description: string;
  features: string[];
  daily_search_limit?: number | null;
}

export interface PlanUpdateInput {
  display_name?: string;
  price_label?: string;
  period?: string | null;
  description?: string;
  features?: string[];
  daily_search_limit?: number | null;
  // PATCH can't tell "left alone" apart from "set to unlimited" for an
  // optional int, so clearing the limit is a dedicated flag (mirrors the
  // backend's PlanUpdateRequest).
  clear_search_limit?: boolean;
}

export interface Usage {
  plan: string;
  limit: number | null; // null = unlimited
  used: number;
  remaining: number | null;
}

export class ApiError extends Error {}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; auth?: boolean; query?: Record<string, string> } = {}
): Promise<T> {
  const { method = "GET", body, auth = false, query } = options;

  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) Object.entries(query).forEach(([key, value]) => url.searchParams.set(key, value));

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url.toString(), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new ApiError(errorBody?.detail ? String(errorBody.detail) : `Request failed (${response.status})`);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function discover(query: string, k = 5): Promise<DiscoverResponse> {
  // auth: true attaches a token when one exists, but never requires it —
  // search stays usable signed-out. When signed in, it's what lets the
  // backend attribute the search to the user for /recommendations.
  return request<DiscoverResponse>("/discover", { method: "POST", query: { query, k: String(k) }, auth: true });
}

export async function getRecommendations(k = 3): Promise<RecommendationResponse> {
  return request<RecommendationResponse>("/recommendations", { query: { k: String(k) }, auth: true });
}

export async function clearSearchHistory(): Promise<void> {
  return request<void>("/recommendations", { method: "DELETE", auth: true });
}

export async function register(name: string, email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/register", { method: "POST", body: { name, email, password } });
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", { method: "POST", body: { email, password } });
}

export async function getCurrentUser(): Promise<User> {
  return request<User>("/auth/me", { auth: true });
}

export async function updateProfile(name: string): Promise<User> {
  return request<User>("/auth/me", { method: "PATCH", body: { name }, auth: true });
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return request<void>("/auth/change-password", {
    method: "POST",
    body: { current_password: currentPassword, new_password: newPassword },
    auth: true,
  });
}

export async function forgotPassword(email: string): Promise<{ message: string; dev_reset_token?: string }> {
  return request("/auth/forgot-password", { method: "POST", body: { email } });
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  return request<void>("/auth/reset-password", {
    method: "POST",
    body: { token, new_password: newPassword },
  });
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  return request<AdminUser[]>("/admin/users", { auth: true });
}

export async function getAdminStats(): Promise<AdminStats> {
  return request<AdminStats>("/admin/stats", { auth: true });
}

export async function updateAdminUser(
  userId: string,
  changes: { plan?: string; is_admin?: boolean }
): Promise<AdminUser> {
  return request<AdminUser>(`/admin/users/${userId}`, { method: "PATCH", body: changes, auth: true });
}

export async function deleteAdminUser(userId: string): Promise<void> {
  return request<void>(`/admin/users/${userId}`, { method: "DELETE", auth: true });
}

export async function getAdminCatalog(): Promise<CatalogDataset[]> {
  return request<CatalogDataset[]>("/admin/catalog", { auth: true });
}

export async function createCatalogDataset(payload: CatalogDatasetInput): Promise<CatalogDataset> {
  return request<CatalogDataset>("/admin/catalog", { method: "POST", body: payload, auth: true });
}

export async function updateCatalogDataset(
  id: string,
  payload: Partial<CatalogDatasetInput>
): Promise<CatalogDataset> {
  return request<CatalogDataset>(`/admin/catalog/${id}`, { method: "PATCH", body: payload, auth: true });
}

export async function deleteCatalogDataset(id: string): Promise<void> {
  return request<void>(`/admin/catalog/${id}`, { method: "DELETE", auth: true });
}

export async function getPlans(): Promise<Plan[]> {
  // Public — the pricing page needs this without requiring login.
  return request<Plan[]>("/plans");
}

export async function getUsage(): Promise<Usage> {
  // auth: true attaches a token when signed in, but the endpoint works
  // signed-out too (usage tracked by IP for anonymous callers).
  return request<Usage>("/usage", { auth: true });
}

export async function getAdminPlans(): Promise<Plan[]> {
  return request<Plan[]>("/admin/plans", { auth: true });
}

export async function createPlan(payload: PlanInput): Promise<Plan> {
  return request<Plan>("/admin/plans", { method: "POST", body: payload, auth: true });
}

export async function updatePlan(id: string, payload: PlanUpdateInput): Promise<Plan> {
  return request<Plan>(`/admin/plans/${id}`, { method: "PATCH", body: payload, auth: true });
}

export async function deletePlan(id: string): Promise<void> {
  return request<void>(`/admin/plans/${id}`, { method: "DELETE", auth: true });
}
