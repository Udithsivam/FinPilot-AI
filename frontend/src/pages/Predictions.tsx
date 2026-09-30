import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { CalendarClock, History, TrendingUp } from "lucide-react";
import { useState } from "react";

import { PredictionCard } from "@/components/ai/PredictionCard";
import { PredictionExplanation } from "@/components/ai/PredictionExplanation";
import { PredictionForm } from "@/components/financial/PredictionForm";
import { PageContainer } from "@/components/layout/PageContainer";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { SavingsPredictionRequest } from "@/types/api";

export function Predictions() {
  const queryClient = useQueryClient();
  const [lastRequest, setLastRequest] = useState<SavingsPredictionRequest | null>(null);

  const predict = useMutation({
    mutationFn: (payload: SavingsPredictionRequest) => api.predictSavings(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["prediction-history"] }),
  });

  const history = useQuery({ queryKey: ["prediction-history"], queryFn: api.predictionHistory });
  const forecast = useQuery({
    queryKey: ["expense-forecast"],
    queryFn: api.expenseForecast,
    retry: false,
  });
  const forecastInsufficientHistory = forecast.error instanceof ApiError && forecast.error.status === 422;

  const cashFlow = useQuery({
    queryKey: ["cash-flow-forecast"],
    queryFn: api.cashFlowForecast,
    retry: false,
  });
  const cashFlowInsufficientHistory = cashFlow.error instanceof ApiError && cashFlow.error.status === 422;

  function handleSubmit(values: SavingsPredictionRequest) {
    setLastRequest(values);
    predict.mutate(values);
  }

  return (
    <PageContainer className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Predictions</h2>
        <p className="text-sm text-muted-foreground">
          Estimate desired monthly savings from a financial profile, using the trained model.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold text-foreground">Financial profile</CardTitle>
          </CardHeader>
          <CardContent>
            <PredictionForm onSubmit={handleSubmit} isSubmitting={predict.isPending} />
          </CardContent>
        </Card>

        <div className="space-y-4">
          {predict.isError ? (
            <ErrorState
              title="Couldn't generate a prediction"
              description={
                predict.error instanceof ApiError
                  ? predict.error.message
                  : "Something went wrong. Please try again."
              }
              onRetry={() => lastRequest && predict.mutate(lastRequest)}
            />
          ) : predict.data ? (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="space-y-4"
            >
              <PredictionCard
                label="Predicted desired savings"
                value={predict.data.predicted_desired_savings}
                description={`Monthly, based on the profile you entered. Model: ${predict.data.model_type} (v${predict.data.model_version})`}
              />
              <PredictionExplanation
                sample={false}
                factors={predict.data.explanation.map((e) => ({
                  factor: e.feature,
                  impact: e.direction === "positive" ? e.impact : -e.impact,
                }))}
              />
            </motion.div>
          ) : (
            <EmptyState
              icon={TrendingUp}
              title="No prediction yet"
              description="Fill in the financial profile and submit to estimate desired savings."
            />
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Expense forecast</CardTitle>
        </CardHeader>
        <CardContent>
          {forecast.isLoading ? (
            <Skeleton className="h-24" />
          ) : forecastInsufficientHistory ? (
            <EmptyState
              icon={CalendarClock}
              title="Not enough history yet"
              description="At least two months of expense transactions are needed to forecast next month's spending."
            />
          ) : forecast.isError ? (
            <ErrorState onRetry={() => forecast.refetch()} />
          ) : forecast.data ? (
            <div className="space-y-2">
              <PredictionCard
                label={`Predicted expense — ${forecast.data.forecast_period}`}
                value={forecast.data.predicted_expense}
                description={`Model: ${forecast.data.model_name} (v${forecast.data.model_version})`}
              />
              <p className="text-xs text-muted-foreground">
                Historical moving-average baseline for comparison: {formatCurrency(forecast.data.baseline_comparison)}
              </p>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Cash-flow forecast</CardTitle>
        </CardHeader>
        <CardContent>
          {cashFlow.isLoading ? (
            <Skeleton className="h-24" />
          ) : cashFlowInsufficientHistory ? (
            <EmptyState
              icon={CalendarClock}
              title="Not enough history yet"
              description="At least two months of income and expense transactions are needed to forecast next month's cash flow."
            />
          ) : cashFlow.isError ? (
            <ErrorState onRetry={() => cashFlow.refetch()} />
          ) : cashFlow.data ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <PredictionCard
                label="Predicted income"
                value={cashFlow.data.predicted_income}
                description={cashFlow.data.forecast_period}
              />
              <PredictionCard
                label="Predicted expense"
                value={cashFlow.data.predicted_expense}
                description={cashFlow.data.forecast_period}
              />
              <PredictionCard
                label="Predicted net cash flow"
                value={cashFlow.data.predicted_net_cash_flow}
                description={`Model: ${cashFlow.data.model_name} (v${cashFlow.data.model_version})`}
              />
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Prediction history</CardTitle>
        </CardHeader>
        <CardContent>
          {history.isLoading ? (
            <Skeleton className="h-24" />
          ) : history.isError ? (
            <ErrorState onRetry={() => history.refetch()} />
          ) : history.data && history.data.length > 0 ? (
            <div className="divide-y divide-border">
              {history.data.map((item) => (
                <div key={item.id} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="capitalize">
                        {item.prediction_type}
                      </Badge>
                      <span className="truncate text-sm font-medium">{item.prediction_value}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {new Date(item.created_at).toLocaleString()} · {item.model_name} (v{item.model_version})
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={History}
              title="No predictions yet"
              description="Every savings prediction and transaction categorization you make is recorded here."
            />
          )}
        </CardContent>
      </Card>
    </PageContainer>
  );
}
