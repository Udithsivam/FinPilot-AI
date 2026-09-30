import type {
  Budget,
  BudgetInput,
  CategorizeRequest,
  CategorizeResponse,
  DashboardSummary,
  FeedbackInput,
  Goal,
  GoalInput,
  HealthScoreResponse,
  Insight,
  MonthlyBreakdown,
  PredictionHistoryItem,
  ProfileUpdate,
  Recommendation,
  SavingsPredictionRequest,
  SavingsPredictionResponse,
  Token,
  Transaction,
  TransactionInput,
  User,
  CategoryAmount,
} from "@/types/api";

const TOKEN_STORAGE_KEY = "finpilot-token";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof URLSearchParams) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`/api${path}`, { ...init, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      /* no JSON body */
    }
    throw new ApiError(response.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  async login(email: string, password: string) {
    const body = new URLSearchParams({ username: email, password });
    return request<Token>("/auth/login", { method: "POST", body });
  },
  async register(email: string, password: string, full_name: string) {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
  },
  me: () => request<User>("/users/me"),
  getProfile: () => request<ProfileUpdate>("/users/me/profile"),
  updateProfile: (payload: ProfileUpdate) =>
    request<ProfileUpdate>("/users/me/profile", { method: "PUT", body: JSON.stringify(payload) }),

  listTransactions: () => request<Transaction[]>("/transactions"),
  createTransaction: (payload: TransactionInput) =>
    request<Transaction>("/transactions", { method: "POST", body: JSON.stringify(payload) }),
  deleteTransaction: (id: number) => request<void>(`/transactions/${id}`, { method: "DELETE" }),
  categorizeTransaction: (payload: CategorizeRequest) =>
    request<CategorizeResponse>("/transactions/categorize", { method: "POST", body: JSON.stringify(payload) }),

  listBudgets: () => request<Budget[]>("/budgets"),
  createBudget: (payload: BudgetInput) =>
    request<Budget>("/budgets", { method: "POST", body: JSON.stringify(payload) }),
  deleteBudget: (id: number) => request<void>(`/budgets/${id}`, { method: "DELETE" }),

  listGoals: () => request<Goal[]>("/goals"),
  createGoal: (payload: GoalInput) =>
    request<Goal>("/goals", { method: "POST", body: JSON.stringify(payload) }),
  deleteGoal: (id: number) => request<void>(`/goals/${id}`, { method: "DELETE" }),

  dashboard: () => request<DashboardSummary>("/analytics/dashboard"),
  monthly: () => request<MonthlyBreakdown[]>("/analytics/monthly"),
  categories: () => request<CategoryAmount[]>("/analytics/categories"),
  healthScore: () => request<HealthScoreResponse>("/analytics/health-score"),
  insights: () => request<Insight[]>("/analytics/insights"),
  recommendations: () => request<Recommendation[]>("/analytics/recommendations"),

  predictSavings: (payload: SavingsPredictionRequest) =>
    request<SavingsPredictionResponse>("/predict/savings", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  predictionHistory: () => request<PredictionHistoryItem[]>("/predictions/history"),

  submitFeedback: (payload: FeedbackInput) =>
    request<void>("/feedback", { method: "POST", body: JSON.stringify(payload) }),
};
