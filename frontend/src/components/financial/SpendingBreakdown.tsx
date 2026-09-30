import { motion } from "framer-motion";
import { PieChart } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { cn, formatCurrency } from "@/lib/utils";
import type { CategoryAmount } from "@/types/api";

const PALETTE = [
  "oklch(62% 0.14 264)",
  "oklch(62% 0.13 152)",
  "oklch(70% 0.14 80)",
  "oklch(62% 0.17 25)",
  "oklch(62% 0.12 200)",
  "oklch(62% 0.14 320)",
];

interface SpendingBreakdownProps {
  data: CategoryAmount[];
  className?: string;
}

export function SpendingBreakdown({ data, className }: SpendingBreakdownProps) {
  if (data.length === 0) {
    return (
      <EmptyState
        icon={PieChart}
        title="No spending yet"
        description="Add expense transactions to see a category breakdown."
        className={className}
      />
    );
  }

  const max = Math.max(...data.map((d) => d.amount));
  const total = data.reduce((sum, d) => sum + d.amount, 0);

  return (
    <div className={cn("space-y-4", className)}>
      {data.map((item, index) => (
        <div key={item.category} className="space-y-1.5">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">{item.category}</span>
            <span className="text-muted-foreground">
              {formatCurrency(item.amount)} · {((item.amount / total) * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(item.amount / max) * 100}%` }}
              transition={{ duration: 0.5, ease: "easeOut", delay: index * 0.05 }}
              className="h-full rounded-full"
              style={{ backgroundColor: PALETTE[index % PALETTE.length] }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
