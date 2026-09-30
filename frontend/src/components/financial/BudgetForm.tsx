import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { BudgetInput } from "@/types/api";

const schema = z.object({
  category: z.string().min(1, "Category is required"),
  amount: z.coerce.number().positive("Amount must be greater than 0"),
  period: z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/, "Pick a month"),
});

interface BudgetFormProps {
  onSubmit: (values: BudgetInput) => Promise<void> | void;
  onCancel?: () => void;
  isSubmitting?: boolean;
}

export function BudgetForm({ onSubmit, onCancel, isSubmitting }: BudgetFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<z.input<typeof schema>, unknown, z.output<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { period: new Date().toISOString().slice(0, 7) },
  });

  const submit = handleSubmit(async (values) => {
    await onSubmit(values);
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="category">Category</Label>
        <Input id="category" placeholder="Groceries" {...register("category")} />
        {errors.category && <p className="text-xs text-danger">{errors.category.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="amount">Monthly limit</Label>
          <Input id="amount" type="number" step="0.01" placeholder="10000" {...register("amount")} />
          {errors.amount && <p className="text-xs text-danger">{errors.amount.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="period">Month</Label>
          <Input id="period" type="month" {...register("period")} />
          {errors.period && <p className="text-xs text-danger">{errors.period.message}</p>}
        </div>
      </div>

      <DialogFooter>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" isLoading={isSubmitting}>
          Save budget
        </Button>
      </DialogFooter>
    </form>
  );
}
