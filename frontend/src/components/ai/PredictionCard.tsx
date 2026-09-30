import { TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";

interface PredictionCardProps {
  label: string;
  value: number;
  description?: string;
  /** Only set this when the value is NOT from a real /predict/* call. */
  sample?: boolean;
}

export function PredictionCard({ label, value, description, sample = false }: PredictionCardProps) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
          <TrendingUp className="size-4 text-ai" />
          {label}
        </CardTitle>
        {sample && <Badge variant="outline">Sample</Badge>}
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-semibold tabular-nums">{formatCurrency(value)}</p>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </CardContent>
    </Card>
  );
}
