/**
 * Sample/preview data only — NOT real model output.
 *
 * Transaction categorization, forecasting, anomaly detection,
 * recommendations and explainability are not implemented on the backend
 * yet (see README "Phase 5"). Everything here exists so the AI
 * components can be built and previewed now; every component that
 * consumes it renders a visible "Sample" badge so it's never mistaken
 * for a live prediction. Replace these with real API responses once the
 * corresponding endpoints exist — do not wire this data into
 * production pages (e.g. the Dashboard).
 */

export const SAMPLE_INSIGHTS = [
  {
    id: "1",
    title: "Dining spend rose 18% this month",
    description: "Eating Out is higher than your 3-month average.",
    tone: "warning" as const,
  },
  {
    id: "2",
    title: "Consistent savings streak",
    description: "You've saved more than 15% of income for 3 months running.",
    tone: "success" as const,
  },
];

export const SAMPLE_RECOMMENDATION = {
  title: "Trim discretionary dining spend",
  detected: "Dining expenses are 22% higher than your average over the last 3 months.",
  why: "Dining is your largest discretionary category, so small reductions have an outsized effect on savings.",
  action: "Set a soft weekly cap on dining out and use Groceries for planned meals instead.",
  impact: "Could increase projected monthly savings by roughly ₹2,000–₹3,000.",
};

export const SAMPLE_ANOMALY = {
  category: "Entertainment",
  amount: 12000,
  typicalRange: "₹500–₹1,200",
  date: "2026-03-14",
};

export const SAMPLE_PREDICTION_EXPLANATION = [
  { factor: "Income", impact: 0.42 },
  { factor: "Rent", impact: -0.21 },
  { factor: "Loan Repayment", impact: -0.15 },
  { factor: "Groceries", impact: -0.09 },
  { factor: "Eating Out", impact: -0.06 },
];
