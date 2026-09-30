import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Plus, Receipt } from "lucide-react";
import { useMemo, useState } from "react";

import { TransactionForm } from "@/components/financial/TransactionForm";
import { TransactionRow } from "@/components/financial/TransactionRow";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "@/components/ui/toaster";
import { api, ApiError } from "@/lib/api";
import type { Transaction, TransactionInput } from "@/types/api";

type Filter = "all" | "income" | "expense";

export function Transactions() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<Filter>("all");
  const [addOpen, setAddOpen] = useState(false);

  const transactions = useQuery({ queryKey: ["transactions"], queryFn: api.listTransactions });

  const createTransaction = useMutation({
    mutationFn: (payload: TransactionInput) => api.createTransaction(payload),
    onSuccess: () => {
      toast.success("Transaction added");
      setAddOpen(false);
      invalidateAll();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Couldn't add transaction"),
  });

  const deleteTransaction = useMutation({
    mutationFn: (id: number) => api.deleteTransaction(id),
    onSuccess: () => {
      toast.success("Transaction deleted");
      invalidateAll();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Couldn't delete transaction"),
  });

  function invalidateAll() {
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    queryClient.invalidateQueries({ queryKey: ["health-score"] });
    queryClient.invalidateQueries({ queryKey: ["monthly"] });
    queryClient.invalidateQueries({ queryKey: ["categories"] });
    queryClient.invalidateQueries({ queryKey: ["budgets"] });
  }

  const filtered = useMemo<Transaction[]>(() => {
    if (!transactions.data) return [];
    if (filter === "all") return transactions.data;
    return transactions.data.filter((t) => t.type === filter);
  }, [transactions.data, filter]);

  return (
    <PageContainer className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Transactions</h2>
          <p className="text-sm text-muted-foreground">Every income and expense you've recorded.</p>
        </div>
        <Button onClick={() => setAddOpen(true)}>
          <Plus />
          Add transaction
        </Button>
      </div>

      <Tabs value={filter} onValueChange={(v) => setFilter(v as Filter)}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="income">Income</TabsTrigger>
          <TabsTrigger value="expense">Expense</TabsTrigger>
        </TabsList>
      </Tabs>

      {transactions.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      ) : transactions.isError ? (
        <ErrorState onRetry={() => transactions.refetch()} />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Receipt}
          title="No transactions yet"
          description="Start tracking your finances to see your spending patterns here."
          action={
            <Button onClick={() => setAddOpen(true)}>
              <Plus />
              Add your first transaction
            </Button>
          }
        />
      ) : (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
          <Card>
            <CardContent className="p-5">
              {filtered.map((transaction) => (
                <TransactionRow
                  key={transaction.id}
                  transaction={transaction}
                  onDelete={(id) => deleteTransaction.mutate(id)}
                />
              ))}
            </CardContent>
          </Card>
        </motion.div>
      )}

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add transaction</DialogTitle>
          </DialogHeader>
          <TransactionForm
            isSubmitting={createTransaction.isPending}
            onCancel={() => setAddOpen(false)}
            onSubmit={(values) => createTransaction.mutate(values)}
          />
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
