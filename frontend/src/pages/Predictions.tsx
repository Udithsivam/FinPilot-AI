import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { History, TrendingUp } from "lucide-react";
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
import type { SavingsPredictionRequest } from "@/types/api";

export function Predictions() {
  const queryClient = useQueryClient();
  const [lastRequest, setLastRequest] = useState<SavingsPredictionRequest | null>(null);

  const predict = useMutation({
    mutationFn: (payload: SavingsPredictionRequest) => api.predictSavings(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["prediction-history"] }),
  });

  const history = useQuery({ queryKey: ["prediction-history"], queryFn: api.predictionHistory });

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
