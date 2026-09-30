import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";

interface AnomalyAlertProps {
  merchant: string | null;
  amount: number;
  category: string;
  reason: string;
  severity: "low" | "medium" | "high";
  date: string;
}

const SEVERITY_LABEL: Record<AnomalyAlertProps["severity"], string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

export function AnomalyAlert({ merchant, amount, category, reason, severity, date }: AnomalyAlertProps) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-warning-subtle bg-warning-subtle/40 p-4">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-warning-subtle text-warning-subtle-foreground">
        <AlertTriangle className="size-4" />
      </div>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium">
            {merchant ? `${merchant} — ` : ""}
            {category}
          </p>
          <Badge variant="outline" className="capitalize">
            {SEVERITY_LABEL[severity]} severity
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {formatCurrency(amount)} on {new Date(date).toLocaleDateString()}
        </p>
        <p className="text-sm text-muted-foreground">{reason}</p>
      </div>
    </div>
  );
}
