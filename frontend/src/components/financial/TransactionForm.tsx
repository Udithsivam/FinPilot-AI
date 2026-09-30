import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { TransactionInput } from "@/types/api";

const schema = z.object({
  date: z.string().min(1, "Date is required"),
  amount: z.coerce.number().positive("Amount must be greater than 0"),
  type: z.enum(["income", "expense"]),
  category: z.string().min(1, "Category is required"),
  subcategory: z.string().optional(),
  merchant: z.string().optional(),
  payment_method: z.string().optional(),
  description: z.string().optional(),
  is_recurring: z.boolean(),
});

interface TransactionFormProps {
  onSubmit: (values: TransactionInput) => Promise<void> | void;
  onCancel?: () => void;
  isSubmitting?: boolean;
}

export function TransactionForm({ onSubmit, onCancel, isSubmitting }: TransactionFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<z.input<typeof schema>, unknown, z.output<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      date: new Date().toISOString().slice(0, 10),
      type: "expense",
      is_recurring: false,
    },
  });

  const submit = handleSubmit(async (values) => {
    await onSubmit({
      ...values,
      subcategory: values.subcategory || null,
      merchant: values.merchant || null,
      payment_method: values.payment_method || null,
      description: values.description || null,
    });
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="date">Date</Label>
          <Input id="date" type="date" {...register("date")} />
          {errors.date && <p className="text-xs text-danger">{errors.date.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="amount">Amount</Label>
          <Input id="amount" type="number" step="0.01" placeholder="0.00" {...register("amount")} />
          {errors.amount && <p className="text-xs text-danger">{errors.amount.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label>Type</Label>
          <Controller
            control={control}
            name="type"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="expense">Expense</SelectItem>
                  <SelectItem value="income">Income</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="category">Category</Label>
          <Input id="category" placeholder="Groceries" {...register("category")} />
          {errors.category && <p className="text-xs text-danger">{errors.category.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="merchant">Merchant</Label>
          <Input id="merchant" placeholder="Optional" {...register("merchant")} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="payment_method">Payment method</Label>
          <Input id="payment_method" placeholder="UPI, Card, Cash..." {...register("payment_method")} />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="description">Description</Label>
        <Input id="description" placeholder="Optional note" {...register("description")} />
      </div>

      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <input type="checkbox" className="size-4 rounded border-input" {...register("is_recurring")} />
        This is a recurring transaction
      </label>

      <DialogFooter>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" isLoading={isSubmitting}>
          Save transaction
        </Button>
      </DialogFooter>
    </form>
  );
}
