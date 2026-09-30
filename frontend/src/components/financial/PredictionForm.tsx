import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { SavingsPredictionRequest } from "@/types/api";

const schema = z.object({
  Income: z.coerce.number().positive("Required"),
  Age: z.coerce.number().int().min(18).max(100),
  Dependents: z.coerce.number().int().min(0),
  Occupation: z.enum(["Student", "Professional", "Self_Employed", "Retired"]),
  City_Tier: z.enum(["Tier_1", "Tier_2", "Tier_3"]),
  Rent: z.coerce.number().min(0),
  Loan_Repayment: z.coerce.number().min(0),
  Insurance: z.coerce.number().min(0),
  Groceries: z.coerce.number().min(0),
  Transport: z.coerce.number().min(0),
  Eating_Out: z.coerce.number().min(0),
  Entertainment: z.coerce.number().min(0),
  Utilities: z.coerce.number().min(0),
  Healthcare: z.coerce.number().min(0),
  Education: z.coerce.number().min(0),
  Miscellaneous: z.coerce.number().min(0),
});

const EXPENSE_FIELDS = [
  "Rent",
  "Loan_Repayment",
  "Insurance",
  "Groceries",
  "Transport",
  "Eating_Out",
  "Entertainment",
  "Utilities",
  "Healthcare",
  "Education",
  "Miscellaneous",
] as const;

const FIELD_LABELS: Record<(typeof EXPENSE_FIELDS)[number], string> = {
  Rent: "Rent",
  Loan_Repayment: "Loan repayment",
  Insurance: "Insurance",
  Groceries: "Groceries",
  Transport: "Transport",
  Eating_Out: "Eating out",
  Entertainment: "Entertainment",
  Utilities: "Utilities",
  Healthcare: "Healthcare",
  Education: "Education",
  Miscellaneous: "Miscellaneous",
};

interface PredictionFormProps {
  onSubmit: (values: SavingsPredictionRequest) => Promise<void> | void;
  isSubmitting?: boolean;
}

export function PredictionForm({ onSubmit, isSubmitting }: PredictionFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<z.input<typeof schema>, unknown, z.output<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { Occupation: "Professional", City_Tier: "Tier_1", Dependents: 0 },
  });

  const submit = handleSubmit(async (values) => {
    await onSubmit(values);
  });

  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="Income">Monthly income</Label>
          <Input id="Income" type="number" step="0.01" placeholder="50000" {...register("Income")} />
          {errors.Income && <p className="text-xs text-danger">{errors.Income.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="Age">Age</Label>
          <Input id="Age" type="number" placeholder="30" {...register("Age")} />
          {errors.Age && <p className="text-xs text-danger">{errors.Age.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="Dependents">Dependents</Label>
          <Input id="Dependents" type="number" placeholder="0" {...register("Dependents")} />
          {errors.Dependents && <p className="text-xs text-danger">{errors.Dependents.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label>City tier</Label>
          <Controller
            control={control}
            name="City_Tier"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Tier_1">Tier 1</SelectItem>
                  <SelectItem value="Tier_2">Tier 2</SelectItem>
                  <SelectItem value="Tier_3">Tier 3</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label>Occupation</Label>
        <Controller
          control={control}
          name="Occupation"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Student">Student</SelectItem>
                <SelectItem value="Professional">Professional</SelectItem>
                <SelectItem value="Self_Employed">Self-employed</SelectItem>
                <SelectItem value="Retired">Retired</SelectItem>
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div>
        <p className="mb-2 text-sm font-medium">Monthly expenses</p>
        <div className="grid grid-cols-2 gap-4">
          {EXPENSE_FIELDS.map((field) => (
            <div key={field} className="space-y-1.5">
              <Label htmlFor={field}>{FIELD_LABELS[field]}</Label>
              <Input id={field} type="number" step="0.01" placeholder="0" {...register(field)} />
              {errors[field] && <p className="text-xs text-danger">{errors[field]?.message}</p>}
            </div>
          ))}
        </div>
      </div>

      <Button type="submit" className="w-full" isLoading={isSubmitting}>
        Predict my savings
      </Button>
    </form>
  );
}
