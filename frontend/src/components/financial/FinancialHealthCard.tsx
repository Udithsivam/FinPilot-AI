import { motion } from "framer-motion";
import { HeartPulse } from "lucide-react";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { HealthRating, HealthScoreResponse } from "@/types/api";
import { cn } from "@/lib/utils";

const RATING_VARIANT: Record<HealthRating, NonNullable<BadgeProps["variant"]>> = {
  Good: "success",
  Moderate: "warning",
  Low: "danger",
  High: "danger",
  "Not Enough Data": "default",
};

function scoreTone(score: number | null) {
  if (score === null) return "var(--color-muted-foreground)";
  if (score >= 70) return "var(--color-success)";
  if (score >= 40) return "var(--color-warning)";
  return "var(--color-danger)";
}

interface FinancialHealthCardProps {
  data: HealthScoreResponse;
  className?: string;
}

export function FinancialHealthCard({ data, className }: FinancialHealthCardProps) {
  const score = data.score;
  const ringColor = scoreTone(score);
  const percentage = score ?? 0;

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
          <HeartPulse className="size-4 text-brand" />
          Financial Health Score
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-6 sm:flex-row sm:items-center">
        <div className="flex shrink-0 justify-center sm:justify-start">
          <div
            className="relative flex size-28 items-center justify-center rounded-full"
            style={{
              background: `conic-gradient(${ringColor} ${percentage * 3.6}deg, var(--color-muted) 0deg)`,
            }}
          >
            <div className="flex size-20 flex-col items-center justify-center rounded-full bg-card">
              <motion.span
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="text-3xl font-bold tabular-nums"
              >
                {score !== null ? Math.round(score) : "—"}
              </motion.span>
              <span className="text-[11px] text-muted-foreground">out of 100</span>
            </div>
          </div>
        </div>

        <ul className="flex-1 space-y-2.5">
          {data.factors.map((factor) => (
            <li key={factor.key} className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium">{factor.label}</p>
                <p className="truncate text-xs text-muted-foreground">{factor.detail}</p>
              </div>
              <Badge variant={RATING_VARIANT[factor.rating]} className="shrink-0">
                {factor.rating}
              </Badge>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
