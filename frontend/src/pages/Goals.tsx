import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Plus, Target } from "lucide-react";
import { useState } from "react";

import { GoalCard } from "@/components/financial/GoalCard";
import { GoalForm } from "@/components/financial/GoalForm";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toaster";
import { api, ApiError } from "@/lib/api";
import type { GoalInput } from "@/types/api";

export function Goals() {
  const queryClient = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);
  const goals = useQuery({ queryKey: ["goals"], queryFn: api.listGoals });

  const createGoal = useMutation({
    mutationFn: (payload: GoalInput) => api.createGoal(payload),
    onSuccess: () => {
      toast.success("Goal created");
      setAddOpen(false);
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["health-score"] });
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Couldn't create goal"),
  });

  const deleteGoal = useMutation({
    mutationFn: (id: number) => api.deleteGoal(id),
    onSuccess: () => {
      toast.success("Goal deleted");
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["health-score"] });
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Couldn't delete goal"),
  });

  return (
    <PageContainer className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Goals</h2>
          <p className="text-sm text-muted-foreground">Track progress toward what you're saving for.</p>
        </div>
        <Button onClick={() => setAddOpen(true)}>
          <Plus />
          Add goal
        </Button>
      </div>

      {goals.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-36" />
          ))}
        </div>
      ) : goals.isError ? (
        <ErrorState onRetry={() => goals.refetch()} />
      ) : goals.data && goals.data.length > 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          {goals.data.map((goal) => (
            <GoalCard key={goal.id} goal={goal} onDelete={(id) => deleteGoal.mutate(id)} />
          ))}
        </motion.div>
      ) : (
        <EmptyState
          icon={Target}
          title="No goals yet"
          description="Set a savings goal to connect your spending to what matters."
          action={
            <Button onClick={() => setAddOpen(true)}>
              <Plus />
              Add your first goal
            </Button>
          }
        />
      )}

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add goal</DialogTitle>
          </DialogHeader>
          <GoalForm
            isSubmitting={createGoal.isPending}
            onCancel={() => setAddOpen(false)}
            onSubmit={(values) => createGoal.mutate(values)}
          />
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
