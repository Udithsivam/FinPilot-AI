import { LineChart as LineChartIcon } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { EmptyState } from "@/components/ui/empty-state";
import { formatCurrency, formatMonthLabel } from "@/lib/utils";
import type { MonthlyBreakdown } from "@/types/api";

const INCOME_COLOR = "oklch(62% 0.13 152)";
const EXPENSE_COLOR = "oklch(62% 0.14 264)";

interface ChartTooltipProps {
  active?: boolean;
  label?: string;
  payload?: { dataKey: string; name: string; value: number; color: string }[];
}

function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length || !label) return null;
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-popover-foreground">{formatMonthLabel(label)}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="text-muted-foreground">
          <span className="font-medium" style={{ color: entry.color }}>
            {entry.name}:
          </span>{" "}
          {formatCurrency(entry.value)}
        </p>
      ))}
    </div>
  );
}

interface CashFlowChartProps {
  data: MonthlyBreakdown[];
  className?: string;
}

export function CashFlowChart({ data, className }: CashFlowChartProps) {
  if (data.length === 0) {
    return (
      <EmptyState
        icon={LineChartIcon}
        title="No cash flow data yet"
        description="Add income and expense transactions to see trends over time."
        className={className}
      />
    );
  }

  return (
    <div className={className} style={{ width: "100%", height: 280 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="incomeGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={INCOME_COLOR} stopOpacity={0.35} />
              <stop offset="95%" stopColor={INCOME_COLOR} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="expenseGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={EXPENSE_COLOR} stopOpacity={0.3} />
              <stop offset="95%" stopColor={EXPENSE_COLOR} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="var(--color-border)" />
          <XAxis
            dataKey="month"
            tickFormatter={formatMonthLabel}
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 12, fill: "var(--color-muted-foreground)" }}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            width={48}
            tick={{ fontSize: 12, fill: "var(--color-muted-foreground)" }}
            tickFormatter={(value) => `${Math.round(value / 1000)}k`}
          />
          <Tooltip content={<ChartTooltip />} />
          <Area
            type="monotone"
            dataKey="income"
            name="Income"
            stroke={INCOME_COLOR}
            strokeWidth={2}
            fill="url(#incomeGradient)"
          />
          <Area
            type="monotone"
            dataKey="expenses"
            name="Expenses"
            stroke={EXPENSE_COLOR}
            strokeWidth={2}
            fill="url(#expenseGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
