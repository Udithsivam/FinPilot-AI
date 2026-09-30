import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, type LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type MetricTone = "brand" | "success" | "warning" | "danger" | "neutral";

interface MetricCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  tone?: MetricTone;
  trend?: { value: number; label?: string };
  className?: string;
}

const toneClasses: Record<MetricTone, string> = {
  brand: "bg-brand-subtle text-brand-subtle-foreground",
  success: "bg-success-subtle text-success-subtle-foreground",
  warning: "bg-warning-subtle text-warning-subtle-foreground",
  danger: "bg-danger-subtle text-danger-subtle-foreground",
  neutral: "bg-muted text-muted-foreground",
};

export function MetricCard({ label, value, icon: Icon, tone = "brand", trend, className }: MetricCardProps) {
  const isPositive = (trend?.value ?? 0) >= 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-start justify-between gap-3 p-5">
          <div className="min-w-0 space-y-1.5">
            <p className="truncate text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-semibold tracking-tight tabular-nums">{value}</p>
            {trend && (
              <div
                className={cn(
                  "flex items-center gap-1 text-xs font-medium",
                  isPositive ? "text-success" : "text-danger",
                )}
              >
                {isPositive ? <ArrowUpRight className="size-3.5" /> : <ArrowDownRight className="size-3.5" />}
                <span>{Math.abs(trend.value).toFixed(1)}%</span>
                {trend.label && <span className="font-normal text-muted-foreground">{trend.label}</span>}
              </div>
            )}
          </div>
          <div className={cn("flex size-10 shrink-0 items-center justify-center rounded-lg", toneClasses[tone])}>
            <Icon className="size-5" />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
