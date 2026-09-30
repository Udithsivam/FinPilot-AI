import { Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { formatCurrency } from "@/lib/utils";
import type { Budget } from "@/types/api";

const STATUS_CONFIG = {
  normal: { label: "On track", badge: "success", bar: "bg-success" },
  approaching_limit: { label: "Approaching limit", badge: "warning", bar: "bg-warning" },
  exceeded: { label: "Exceeded", badge: "danger", bar: "bg-danger" },
} as const;

interface BudgetCardProps {
  budget: Budget;
  onDelete?: (id: number) => void;
}

export function BudgetCard({ budget, onDelete }: BudgetCardProps) {
  const status = STATUS_CONFIG[budget.status];

  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-medium">{budget.category}</p>
            <p className="text-xs text-muted-foreground">{budget.period}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={status.badge}>{status.label}</Badge>
            {onDelete && (
              <Button
                variant="ghost"
                size="icon"
                className="size-7 text-muted-foreground hover:text-danger"
                onClick={() => onDelete(budget.id)}
                aria-label="Delete budget"
              >
                <Trash2 className="size-3.5" />
              </Button>
            )}
          </div>
        </div>

        <Progress value={Math.min(budget.utilization_pct, 100)} indicatorClassName={status.bar} />

        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {formatCurrency(budget.spent)} of {formatCurrency(budget.amount)}
          </span>
          <span className={budget.remaining < 0 ? "font-medium text-danger" : "font-medium text-foreground"}>
            {budget.remaining < 0
              ? `${formatCurrency(Math.abs(budget.remaining))} over`
              : `${formatCurrency(budget.remaining)} left`}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
