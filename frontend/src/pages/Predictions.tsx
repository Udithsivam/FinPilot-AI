import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";
import { useState } from "react";

import { PredictionCard } from "@/components/ai/PredictionCard";
import { PredictionExplanation } from "@/components/ai/PredictionExplanation";
import { PredictionForm } from "@/components/financial/PredictionForm";
import { PageContainer } from "@/components/layout/PageContainer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { api, ApiError } from "@/lib/api";
import { SAMPLE_PREDICTION_EXPLANATION } from "@/mocks/ai";
import type { SavingsPredictionRequest } from "@/types/api";

export function Predictions() {
  const [lastRequest, setLastRequest] = useState<SavingsPredictionRequest | null>(null);

  const predict = useMutation({
    mutationFn: (payload: SavingsPredictionRequest) => api.predictSavings(payload),
  });

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
                description="Monthly, based on the profile you entered."
              />
              <PredictionExplanation factors={SAMPLE_PREDICTION_EXPLANATION} />
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
    </PageContainer>
  );
}
