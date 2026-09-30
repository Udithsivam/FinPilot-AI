import { useQuery } from "@tanstack/react-query";
import { PiggyBank, TrendingDown, TrendingUp, Wallet } from "lucide-react";

import { CashFlowChart } from "@/components/financial/CashFlowChart";
import { MetricCard } from "@/components/financial/MetricCard";
import { SpendingBreakdown } from "@/components/financial/SpendingBreakdown";
import { PageContainer } from "@/components/layout/PageContainer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";

export function Analytics() {
  const summary = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const monthly = useQuery({ queryKey: ["monthly"], queryFn: api.monthly });
  const categories = useQuery({ queryKey: ["categories"], queryFn: api.categories });

  return (
    <PageContainer className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Analytics</h2>
        <p className="text-sm text-muted-foreground">
          A closer look at your cash flow and spending over time.
        </p>
      </div>

      {summary.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : summary.isError ? (
        <ErrorState onRetry={() => summary.refetch()} />
      ) : summary.data ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            label="Total income"
            value={formatCurrency(summary.data.total_income)}
            icon={TrendingUp}
            tone="success"
          />
          <MetricCard
            label="Total expenses"
            value={formatCurrency(summary.data.total_expenses)}
            icon={TrendingDown}
            tone="danger"
          />
          <MetricCard
            label="Net cash flow"
            value={formatCurrency(summary.data.net_cash_flow)}
            icon={Wallet}
            tone={summary.data.net_cash_flow >= 0 ? "brand" : "danger"}
          />
          <MetricCard
            label="Savings rate"
            value={formatPercent(summary.data.savings_rate)}
            icon={PiggyBank}
            tone="brand"
          />
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Cash flow over time</CardTitle>
        </CardHeader>
        <CardContent>
          {monthly.isLoading ? (
            <Skeleton className="h-[340px]" />
          ) : monthly.isError ? (
            <ErrorState onRetry={() => monthly.refetch()} />
          ) : (
            <CashFlowChart data={monthly.data ?? []} height={340} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Spending by category</CardTitle>
        </CardHeader>
        <CardContent>
          {categories.isLoading ? (
            <Skeleton className="h-64" />
          ) : categories.isError ? (
            <ErrorState onRetry={() => categories.refetch()} />
          ) : (
            <SpendingBreakdown data={categories.data ?? []} />
          )}
        </CardContent>
      </Card>
    </PageContainer>
  );
}
