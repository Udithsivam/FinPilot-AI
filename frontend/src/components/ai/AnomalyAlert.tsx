import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";

interface AnomalyAlertProps {
  category: string;
  amount: number;
  typicalRange: string;
  date: string;
  /** Anomaly detection isn't implemented on the backend yet — defaults true. */
  sample?: boolean;
}

export function AnomalyAlert({ category, amount, typicalRange, date, sample = true }: AnomalyAlertProps) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-warning-subtle bg-warning-subtle/40 p-4">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-warning-subtle text-warning-subtle-foreground">
        <AlertTriangle className="size-4" />
      </div>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium">Unusual {category} spending</p>
          {sample && <Badge variant="outline">Sample</Badge>}
        </div>
        <p className="text-sm text-muted-foreground">
          {formatCurrency(amount)} on {new Date(date).toLocaleDateString()} — well above your typical{" "}
          {typicalRange}.
        </p>
      </div>
    </div>
  );
}
