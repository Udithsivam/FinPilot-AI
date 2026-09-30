import { motion } from "framer-motion";
import { Info } from "lucide-react";

import { AIInsightCard } from "@/components/ai/AIInsightCard";
import { AnomalyAlert } from "@/components/ai/AnomalyAlert";
import { FinancialInsight } from "@/components/ai/FinancialInsight";
import { RecommendationCard } from "@/components/ai/RecommendationCard";
import { PageContainer } from "@/components/layout/PageContainer";
import { SAMPLE_ANOMALY, SAMPLE_INSIGHTS, SAMPLE_RECOMMENDATION } from "@/mocks/ai";

export function AIInsights() {
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
          This section previews what AI Insights will look like. The insight engine isn't built yet, so
          everything below is sample content, clearly marked — not analysis of your real data.
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
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {SAMPLE_INSIGHTS.map((insight) => (
              <AIInsightCard
                key={insight.id}
                title={insight.title}
                description={insight.description}
                tone={insight.tone}
              />
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h3 className="text-base font-semibold">Recommendation</h3>
          <RecommendationCard {...SAMPLE_RECOMMENDATION} />
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
