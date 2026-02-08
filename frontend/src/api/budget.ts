import { apiGet, apiPost } from "./client";

export interface BudgetStatus {
  user_id: string;
  budget_limit: number | null;
  wallet_balance: number;
  currency: string;
}

export async function setBudget(budget_limit: number, currency = "USD", user_id = "demo"): Promise<BudgetStatus> {
  return apiPost<BudgetStatus>("/api/budget/set", { user_id, budget_limit, currency });
}

export async function fetchBudgetStatus(user_id = "demo"): Promise<BudgetStatus> {
  return apiGet<BudgetStatus>(`/api/budget/status?user_id=${encodeURIComponent(user_id)}`);
}

export async function proposePurchase(amount: number, item_name: string, user_id = "demo") {
  return apiPost<{ result: string }>("/api/budget/propose", { user_id, amount, item_name });
}

export async function confirmPurchase(amount: number, user_id = "demo") {
  return apiPost<BudgetStatus>("/api/budget/confirm", { user_id, amount });
}
