import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Info, Lightbulb, Sparkles } from "lucide-react";

import { AIInsightCard } from "@/components/ai/AIInsightCard";
import { AnomalyAlert } from "@/components/ai/AnomalyAlert";
import { FinancialInsight } from "@/components/ai/FinancialInsight";
import { RecommendationCard } from "@/components/ai/RecommendationCard";
import { PageContainer } from "@/components/layout/PageContainer";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { SAMPLE_ANOMALY } from "@/mocks/ai";

export function AIInsights() {
  const insights = useQuery({ queryKey: ["insights"], queryFn: api.insights });
  const recommendations = useQuery({ queryKey: ["recommendations"], queryFn: api.recommendations });

  return (
    <PageContainer className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">AI Insights</h2>
        <p className="text-sm text-muted-foreground">
          Automatic categorization, anomaly detection and recommendations.
        </p>
      </div>

      <div className="flex items-start gap-3 rounded-xl border border-border bg-muted/50 p-4 text-sm">
        <Info className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
        <p className="text-muted-foreground">
          "Recent insights" and "Recommendation" below are computed directly from your own transactions
          and budgets — rule-based, not an AI/ML model. Anomaly detection and the generic financial tip
          are previews of features not built yet, and are clearly marked "Sample".
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="space-y-6"
      >
        <section className="space-y-3">
          <h3 className="text-base font-semibold">Recent insights</h3>
          {insights.isLoading ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Skeleton className="h-20" />
              <Skeleton className="h-20" />
            </div>
          ) : insights.isError ? (
            <ErrorState onRetry={() => insights.refetch()} />
          ) : insights.data && insights.data.length > 0 ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {insights.data.map((insight) => (
                <AIInsightCard
                  key={insight.title}
                  title={insight.title}
                  description={insight.description}
                  tone={insight.tone}
                  sample={false}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Sparkles}
              title="Not enough history yet"
              description="Add a couple months of transactions to see spending-change and savings-streak insights here."
            />
          )}
        </section>

        <section className="space-y-3">
          <h3 className="text-base font-semibold">Recommendations</h3>
          {recommendations.isLoading ? (
            <Skeleton className="h-32" />
          ) : recommendations.isError ? (
            <ErrorState onRetry={() => recommendations.refetch()} />
          ) : recommendations.data && recommendations.data.length > 0 ? (
            <div className="space-y-3">
              {recommendations.data.map((rec) => (
                <RecommendationCard
                  key={rec.id}
                  title={rec.title}
                  detected={rec.evidence}
                  why={rec.reason}
                  action={rec.action}
                  impact={`Priority: ${rec.priority}`}
                  sample={false}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Lightbulb}
              title="No recommendations right now"
              description="Recommendations appear once there's enough budget, spending or income history to evaluate."
            />
          )}
        </section>

        <section className="space-y-3">
          <h3 className="text-base font-semibold">Anomaly detected</h3>
          <AnomalyAlert {...SAMPLE_ANOMALY} />
        </section>

        <section className="space-y-3">
          <h3 className="text-base font-semibold">Financial insight</h3>
          <FinancialInsight text="Users with a similar income and expense profile typically keep 3-6 months of expenses in an emergency fund." />
        </section>
      </motion.div>
    </PageContainer>
  );
}
