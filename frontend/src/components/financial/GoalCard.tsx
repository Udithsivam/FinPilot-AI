import { Target, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { formatCurrency } from "@/lib/utils";
import type { Goal } from "@/types/api";

interface GoalCardProps {
  goal: Goal;
  onDelete?: (id: number) => void;
}

export function GoalCard({ goal, onDelete }: GoalCardProps) {
  const progress = Math.min(goal.progress_pct, 100);

  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-lg bg-brand-subtle">
              <Target className="size-4 text-brand-subtle-foreground" />
            </div>
            <div>
              <p className="font-medium">{goal.name}</p>
              {goal.target_date && (
                <p className="text-xs text-muted-foreground">
                  Target {new Date(goal.target_date).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="size-7 text-muted-foreground hover:text-danger"
              onClick={() => onDelete(goal.id)}
              aria-label="Delete goal"
            >
              <Trash2 className="size-3.5" />
            </Button>
          )}
        </div>

        <Progress value={progress} />

        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {formatCurrency(goal.current_amount)} of {formatCurrency(goal.target_amount)}
          </span>
          <span className="font-medium text-brand">{progress.toFixed(0)}%</span>
        </div>
      </CardContent>
    </Card>
  );
}
