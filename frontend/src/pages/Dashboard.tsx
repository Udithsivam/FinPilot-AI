import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, TrendingDown, TrendingUp, Wallet, PiggyBank } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { BudgetCard } from "@/components/financial/BudgetCard";
import { CashFlowChart } from "@/components/financial/CashFlowChart";
import { FinancialHealthCard } from "@/components/financial/FinancialHealthCard";
import { GoalCard } from "@/components/financial/GoalCard";
import { MetricCard } from "@/components/financial/MetricCard";
import { SpendingBreakdown } from "@/components/financial/SpendingBreakdown";
import { TransactionForm } from "@/components/financial/TransactionForm";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toaster";
import { useAuth } from "@/hooks/use-auth";
import { api, ApiError } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { TransactionInput } from "@/types/api";

function useDashboardData() {
  const summary = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const health = useQuery({ queryKey: ["health-score"], queryFn: api.healthScore });
  const monthly = useQuery({ queryKey: ["monthly"], queryFn: api.monthly });
  const categories = useQuery({ queryKey: ["categories"], queryFn: api.categories });
  const budgets = useQuery({ queryKey: ["budgets"], queryFn: api.listBudgets });
  const goals = useQuery({ queryKey: ["goals"], queryFn: api.listGoals });
  return { summary, health, monthly, categories, budgets, goals };
}

export function Dashboard() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [addTransactionOpen, setAddTransactionOpen] = useState(false);
  const { summary, health, monthly, categories, budgets, goals } = useDashboardData();

  const createTransaction = useMutation({
    mutationFn: (payload: TransactionInput) => api.createTransaction(payload),
    onSuccess: () => {
      toast.success("Transaction added");
      setAddTransactionOpen(false);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["health-score"] });
      queryClient.invalidateQueries({ queryKey: ["monthly"] });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Couldn't add transaction");
    },
  });

  const firstName = user?.full_name?.split(" ")[0];

  return (
    <PageContainer className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">
            {firstName ? `Welcome back, ${firstName}` : "Welcome back"}
          </h2>
          <p className="text-sm text-muted-foreground">Here's where your money stands today.</p>
        </div>
        <Button onClick={() => setAddTransactionOpen(true)}>
          <Plus />
          Add transaction
        </Button>
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

      {health.isLoading ? (
        <Skeleton className="h-56" />
      ) : health.isError ? (
        <ErrorState onRetry={() => health.refetch()} />
      ) : health.data ? (
        <FinancialHealthCard data={health.data} />
      ) : null}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-foreground">Cash flow over time</CardTitle>
          </CardHeader>
          <CardContent>
            {monthly.isLoading ? (
              <Skeleton className="h-64" />
            ) : monthly.isError ? (
              <ErrorState onRetry={() => monthly.refetch()} />
            ) : (
              <CashFlowChart data={monthly.data ?? []} />
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
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold">Budgets</h3>
            <Button variant="link" size="sm" asChild>
              <Link to="/budgets">View all</Link>
            </Button>
          </div>
          {budgets.isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-28" />
              <Skeleton className="h-28" />
            </div>
          ) : budgets.isError ? (
            <ErrorState onRetry={() => budgets.refetch()} />
          ) : budgets.data && budgets.data.length > 0 ? (
            <div className="space-y-3">
              {budgets.data.slice(0, 3).map((budget) => (
                <BudgetCard key={budget.id} budget={budget} />
              ))}
            </div>
          ) : (
            <EmptyState icon={Wallet} title="No budgets yet" description="Set a budget to track spending limits." />
          )}
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold">Goals</h3>
            <Button variant="link" size="sm" asChild>
              <Link to="/goals">View all</Link>
            </Button>
          </div>
          {goals.isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-28" />
              <Skeleton className="h-28" />
            </div>
          ) : goals.isError ? (
            <ErrorState onRetry={() => goals.refetch()} />
          ) : goals.data && goals.data.length > 0 ? (
            <div className="space-y-3">
              {goals.data.slice(0, 3).map((goal) => (
                <GoalCard key={goal.id} goal={goal} />
              ))}
            </div>
          ) : (
            <EmptyState icon={PiggyBank} title="No goals yet" description="Set a savings goal to track progress." />
          )}
        </section>
      </div>

      <Dialog open={addTransactionOpen} onOpenChange={setAddTransactionOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add transaction</DialogTitle>
          </DialogHeader>
          <TransactionForm
            isSubmitting={createTransaction.isPending}
            onCancel={() => setAddTransactionOpen(false)}
            onSubmit={(values) => createTransaction.mutate(values)}
          />
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
