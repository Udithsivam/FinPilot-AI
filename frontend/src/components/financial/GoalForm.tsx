import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { GoalInput } from "@/types/api";

const schema = z.object({
  name: z.string().min(1, "Goal name is required"),
  target_amount: z.coerce.number().positive("Target must be greater than 0"),
  current_amount: z.coerce.number().min(0, "Can't be negative").optional(),
  target_date: z.string().optional(),
});

interface GoalFormProps {
  onSubmit: (values: GoalInput) => Promise<void> | void;
  onCancel?: () => void;
  isSubmitting?: boolean;
}

export function GoalForm({ onSubmit, onCancel, isSubmitting }: GoalFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<z.input<typeof schema>, unknown, z.output<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { current_amount: 0 },
  });

  const submit = handleSubmit(async (values) => {
    await onSubmit({ ...values, target_date: values.target_date || null });
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="name">Goal name</Label>
        <Input id="name" placeholder="Emergency Fund" {...register("name")} />
        {errors.name && <p className="text-xs text-danger">{errors.name.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="target_amount">Target amount</Label>
          <Input id="target_amount" type="number" step="0.01" placeholder="100000" {...register("target_amount")} />
          {errors.target_amount && <p className="text-xs text-danger">{errors.target_amount.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="current_amount">Already saved</Label>
          <Input id="current_amount" type="number" step="0.01" placeholder="0" {...register("current_amount")} />
          {errors.current_amount && <p className="text-xs text-danger">{errors.current_amount.message}</p>}
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="target_date">Target date (optional)</Label>
        <Input id="target_date" type="date" {...register("target_date")} />
      </div>

      <DialogFooter>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" isLoading={isSubmitting}>
          Save goal
        </Button>
      </DialogFooter>
    </form>
  );
}
