import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Info, Lightbulb, ShieldAlert, Sparkles } from "lucide-react";

import { AIChatPanel } from "@/components/ai/AIChatPanel";
import { AIInsightCard } from "@/components/ai/AIInsightCard";
import { AnomalyAlert } from "@/components/ai/AnomalyAlert";
import { RecommendationCard } from "@/components/ai/RecommendationCard";
import { PageContainer } from "@/components/layout/PageContainer";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";

export function AIInsights() {
  const insights = useQuery({ queryKey: ["insights"], queryFn: api.insights });
  const recommendations = useQuery({ queryKey: ["recommendations"], queryFn: api.recommendations });
  const anomalies = useQuery({ queryKey: ["anomalies"], queryFn: api.anomalies });

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
          "Recent insights" and "Recommendations" are computed directly from your own transactions and
          budgets — rule-based, not an AI/ML model. Anomalies are detected with a statistical baseline
          and an Isolation Forest model trained on your own transaction history.
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
          <h3 className="text-base font-semibold">Anomalies</h3>
          {anomalies.isLoading ? (
            <Skeleton className="h-24" />
          ) : anomalies.isError ? (
            <ErrorState onRetry={() => anomalies.refetch()} />
          ) : anomalies.data && anomalies.data.length > 0 ? (
            <div className="space-y-3">
              {anomalies.data.map((a) => (
                <AnomalyAlert
                  key={a.transaction_id}
                  merchant={a.merchant}
                  amount={a.amount}
                  category={a.category}
                  reason={a.reason}
                  severity={a.severity}
                  date={a.date}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={ShieldAlert}
              title="No anomalies detected"
              description="Either your spending looks consistent with your own history, or there isn't yet enough transaction history per category to establish what's typical for you."
            />
          )}
        </section>

        <section className="space-y-3">
          <h3 className="text-base font-semibold">Financial assistant</h3>
          <AIChatPanel />
        </section>
      </motion.div>
    </PageContainer>
  );
}
