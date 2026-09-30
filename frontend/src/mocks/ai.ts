/**
 * Sample/preview data only — NOT real model output.
 *
 * Anomaly detection, expense forecasting and cash-flow prediction are
 * not implemented on the backend yet (see README). Transaction
 * categorization, recommendations, and savings-prediction
 * explainability ARE real now (see src/categorization/,
 * backend/app/services/recommendation_service.py,
 * src/pipeline/explain.py) — their sample data has been removed from
 * this file; don't add it back.
 *
 * Everything remaining here exists so the still-unbuilt AI components
 * can be previewed now; every component that consumes it renders a
 * visible "Sample" badge so it's never mistaken for a live prediction.
 * Do not wire this data into production pages (e.g. the Dashboard).
 */

export const SAMPLE_ANOMALY = {
  category: "Entertainment",
  amount: 12000,
  typicalRange: "₹500–₹1,200",
  date: "2026-03-14",
};
