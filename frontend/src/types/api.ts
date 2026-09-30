export interface User {
  id: number;
  email: string;
  full_name: string;
}

export interface ProfileUpdate {
  user_type?: string;
  age_range?: string;
  monthly_income?: number;
  currency?: string;
  monthly_budget?: number;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export type TransactionType = "income" | "expense";

export interface Transaction {
  id: number;
  date: string;
  amount: number;
  type: TransactionType;
  category: string;
  subcategory: string | null;
  merchant: string | null;
  payment_method: string | null;
  description: string | null;
  is_recurring: boolean;
}

export type TransactionInput = Omit<Transaction, "id">;

export type BudgetStatusLevel = "normal" | "approaching_limit" | "exceeded";

export interface Budget {
  id: number;
  category: string;
  amount: number;
  period: string;
  spent: number;
  remaining: number;
  utilization_pct: number;
  status: BudgetStatusLevel;
}

export interface BudgetInput {
  category: string;
  amount: number;
  period: string;
}

export interface Goal {
  id: number;
  name: string;
  target_amount: number;
  current_amount: number;
  target_date: string | null;
  progress_pct: number;
}

export interface GoalInput {
  name: string;
  target_amount: number;
  current_amount?: number;
  target_date?: string | null;
}

export interface CategoryAmount {
  category: string;
  amount: number;
}

export interface DashboardSummary {
  total_income: number;
  total_expenses: number;
  net_cash_flow: number;
  savings: number;
  savings_rate: number;
  top_categories: CategoryAmount[];
}

export interface MonthlyBreakdown {
  month: string;
  income: number;
  expenses: number;
}

export interface Insight {
  title: string;
  description: string;
  tone: "success" | "warning";
}

export type HealthRating = "Good" | "Moderate" | "Low" | "High" | "Not Enough Data";

export interface HealthScoreFactor {
  key: string;
  label: string;
  rating: HealthRating;
  score: number | null;
  detail: string;
}

export interface HealthScoreResponse {
  score: number | null;
  factors: HealthScoreFactor[];
}

export interface SavingsPredictionRequest {
  Income: number;
  Age: number;
  Dependents: number;
  Occupation: "Student" | "Professional" | "Self_Employed" | "Retired";
  City_Tier: "Tier_1" | "Tier_2" | "Tier_3";
  Rent: number;
  Loan_Repayment: number;
  Insurance: number;
  Groceries: number;
  Transport: number;
  Eating_Out: number;
  Entertainment: number;
  Utilities: number;
  Healthcare: number;
  Education: number;
  Miscellaneous: number;
}

export interface SavingsPredictionResponse {
  predicted_desired_savings: number;
  model_type: string;
  model_version: string;
}
