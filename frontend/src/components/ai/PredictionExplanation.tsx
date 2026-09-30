import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface FactorImpact {
  factor: string;
  /** -1..1, sign indicates direction of influence. */
  impact: number;
}

interface PredictionExplanationProps {
  factors: FactorImpact[];
  /** Backend has no real explainability yet (SHAP/feature importance) — defaults true. */
  sample?: boolean;
}

export function PredictionExplanation({ factors, sample = true }: PredictionExplanationProps) {
  const max = Math.max(...factors.map((f) => Math.abs(f.impact)), 0.0001);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-sm font-medium text-foreground">What influenced this prediction</CardTitle>
        {sample && <Badge variant="outline">Sample</Badge>}
      </CardHeader>
      <CardContent className="space-y-2.5">
        {factors.map((f) => {
          const positive = f.impact >= 0;
          const width = (Math.abs(f.impact) / max) * 100;
          return (
            <div key={f.factor} className="flex items-center gap-3 text-sm">
              <span className="w-28 shrink-0 truncate text-muted-foreground">{f.factor}</span>
              <div className="h-2 flex-1 rounded-full bg-muted">
                <div
                  className={cn("h-full rounded-full", positive ? "bg-success" : "bg-danger")}
                  style={{ width: `${width}%` }}
                />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
