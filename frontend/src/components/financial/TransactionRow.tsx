import { ArrowDownLeft, ArrowUpRight, Repeat, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import type { Transaction } from "@/types/api";

interface TransactionRowProps {
  transaction: Transaction;
  onDelete?: (id: number) => void;
}

export function TransactionRow({ transaction, onDelete }: TransactionRowProps) {
  const isIncome = transaction.type === "income";

  return (
    <div className="flex items-center gap-3 border-b border-border py-3 last:border-0">
      <div
        className={
          "flex size-9 shrink-0 items-center justify-center rounded-full " +
          (isIncome ? "bg-success-subtle text-success-subtle-foreground" : "bg-muted text-muted-foreground")
        }
      >
        {isIncome ? <ArrowDownLeft className="size-4" /> : <ArrowUpRight className="size-4" />}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <p className="truncate text-sm font-medium">{transaction.merchant || transaction.category}</p>
          {transaction.is_recurring && <Repeat className="size-3 shrink-0 text-muted-foreground" />}
        </div>
        <p className="truncate text-xs text-muted-foreground">
          {transaction.category}
          {transaction.subcategory ? ` · ${transaction.subcategory}` : ""} ·{" "}
          {new Date(transaction.date).toLocaleDateString()}
        </p>
      </div>

      <p className={"shrink-0 text-sm font-semibold tabular-nums " + (isIncome ? "text-success" : "text-foreground")}>
        {isIncome ? "+" : "-"}
        {formatCurrency(transaction.amount)}
      </p>

      {onDelete && (
        <Button
          variant="ghost"
          size="icon"
          className="size-7 shrink-0 text-muted-foreground hover:text-danger"
          onClick={() => onDelete(transaction.id)}
          aria-label="Delete transaction"
        >
          <Trash2 className="size-3.5" />
        </Button>
      )}
    </div>
  );
}
