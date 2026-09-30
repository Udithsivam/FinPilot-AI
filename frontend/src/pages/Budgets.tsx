import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Plus, Wallet } from "lucide-react";
import { useState } from "react";

import { BudgetCard } from "@/components/financial/BudgetCard";
import { BudgetForm } from "@/components/financial/BudgetForm";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toaster";
import { api, ApiError } from "@/lib/api";
import type { BudgetInput } from "@/types/api";

export function Budgets() {
  const queryClient = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);
  const budgets = useQuery({ queryKey: ["budgets"], queryFn: api.listBudgets });

  const createBudget = useMutation({
    mutationFn: (payload: BudgetInput) => api.createBudget(payload),
    onSuccess: () => {
      toast.success("Budget created");
      setAddOpen(false);
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["health-score"] });
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Couldn't create budget"),
  });

  const deleteBudget = useMutation({
    mutationFn: (id: number) => api.deleteBudget(id),
    onSuccess: () => {
      toast.success("Budget deleted");
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["health-score"] });
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Couldn't delete budget"),
  });

  return (
    <PageContainer className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Budgets</h2>
          <p className="text-sm text-muted-foreground">Set spending limits and track how close you are.</p>
        </div>
        <Button onClick={() => setAddOpen(true)}>
          <Plus />
          Add budget
        </Button>
      </div>

      {budgets.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-36" />
          ))}
        </div>
      ) : budgets.isError ? (
        <ErrorState onRetry={() => budgets.refetch()} />
      ) : budgets.data && budgets.data.length > 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          {budgets.data.map((budget) => (
            <BudgetCard key={budget.id} budget={budget} onDelete={(id) => deleteBudget.mutate(id)} />
          ))}
        </motion.div>
      ) : (
        <EmptyState
          icon={Wallet}
          title="No budgets yet"
          description="Set a budget to track spending limits by category."
          action={
            <Button onClick={() => setAddOpen(true)}>
              <Plus />
              Add your first budget
            </Button>
          }
        />
      )}

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add budget</DialogTitle>
          </DialogHeader>
          <BudgetForm
            isSubmitting={createBudget.isPending}
            onCancel={() => setAddOpen(false)}
            onSubmit={(values) => createBudget.mutate(values)}
          />
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
