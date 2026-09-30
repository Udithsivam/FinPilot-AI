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

export interface SemanticSearchResult {
  transaction_id: number;
  merchant: string | null;
  description: string | null;
  category: string;
  amount: number;
  date: string;
  similarity: number;
}

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

export interface Recommendation {
  id: number;
  type: string;
  title: string;
  evidence: string;
  reason: string;
  action: string;
  priority: "high" | "medium" | "low";
  created_at: string;
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

export interface FeatureImpact {
  feature: string;
  impact: number;
  direction: "positive" | "negative";
}

export interface SavingsPredictionResponse {
  predicted_desired_savings: number;
  model_type: string;
  model_version: string;
  explanation: FeatureImpact[];
}

export interface PredictionHistoryItem {
  id: number;
  prediction_type: string;
  prediction_value: string;
  model_name: string;
  model_version: string;
  created_at: string;
  actual_value: string | null;
  status: string;
}

export interface CategorizeRequest {
  merchant?: string | null;
  description?: string | null;
}

export interface CategorizeResponse {
  prediction_id: number;
  category: string;
  subcategory: string;
  confidence: number;
  needs_review: boolean;
  model_version: string;
}

export interface AnomalyTransaction {
  transaction_id: number;
  merchant: string | null;
  amount: number;
  category: string;
  date: string;
  method: "statistical_zscore" | "isolation_forest" | "statistical_zscore+isolation_forest";
  anomaly_score: number;
  severity: "low" | "medium" | "high";
  reason: string;
  expected_range: string | null;
}

export interface CashFlowForecastResponse {
  prediction_id: number;
  forecast_period: string;
  predicted_income: number;
  predicted_expense: number;
  predicted_net_cash_flow: number;
  baseline_comparison: number;
  model_name: string;
  model_version: string;
  created_at: string;
}

export interface ExpenseForecastResponse {
  prediction_id: number;
  forecast_period: string;
  predicted_expense: number;
  baseline_comparison: number;
  model_name: string;
  model_version: string;
  created_at: string;
}

export interface ModelVersionInfo {
  name: string;
  version: string;
  run_id: string;
  lifecycle_stage: "candidate" | "validated" | "production" | "archived";
  created_at: number;
}

export interface PerformanceMetric {
  prediction_type: string;
  model_name: string | null;
  model_version: string | null;
  sample_count: number;
  status: "healthy" | "insufficient_data";
  mae: number | null;
  rmse: number | null;
  r2: number | null;
}

export interface DriftMetric {
  feature: string;
  metric: string;
  value: number | null;
  threshold: number | null;
  status: "stable" | "warning" | "drift_detected" | "insufficient_data";
  reference_size: number;
  current_size: number;
}

export interface MLOpsSummary {
  registry: Record<string, ModelVersionInfo[]>;
  performance: PerformanceMetric[];
  drift: DriftMetric[];
  feedback: { total_feedback: number; category_corrections: number; note: string };
  rag: { document_count: number; chunk_count: number; embedding_method: string };
}

export interface ChatSource {
  index: number;
  title: string;
  source: string;
  document_id: string;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  user_facts: string[];
  predictions: string[];
  provider: string;
}

export interface FeedbackInput {
  prediction_id?: number | null;
  feedback_type: "category_correction" | "prediction_correction" | "recommendation_feedback";
  corrected_value?: string | null;
}
