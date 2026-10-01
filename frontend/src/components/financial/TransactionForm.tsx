import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Camera, Sparkles } from "lucide-react";
import { useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/components/ui/toaster";
import { api, ApiError } from "@/lib/api";
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
  const [suggestion, setSuggestion] = useState<{
    predictionId: number;
    category: string;
    subcategory: string;
    confidence: number;
    needsReview: boolean;
  } | null>(null);
  const [scannedText, setScannedText] = useState<string | null>(null);
  const receiptInputRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    control,
    getValues,
    setValue,
    formState: { errors },
  } = useForm<z.input<typeof schema>, unknown, z.output<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      date: new Date().toISOString().slice(0, 10),
      type: "expense",
      is_recurring: false,
    },
  });

  const categorize = useMutation({
    mutationFn: () =>
      api.categorizeTransaction({
        merchant: getValues("merchant") || null,
        description: getValues("description") || null,
      }),
    onSuccess: (result) => {
      setValue("category", result.category, { shouldValidate: true });
      setValue("subcategory", result.subcategory);
      setSuggestion({
        predictionId: result.prediction_id,
        category: result.category,
        subcategory: result.subcategory,
        confidence: result.confidence,
        needsReview: result.needs_review,
      });
    },
  });

  const scanReceipt = useMutation({
    mutationFn: (file: File) => api.scanReceipt(file),
    onSuccess: (result) => {
      // Only prefill fields OCR actually extracted with confidence — an
      // untouched field stays exactly as the user left it rather than
      // being overwritten with a guess.
      if (result.merchant) setValue("merchant", result.merchant);
      if (result.amount !== null) setValue("amount", result.amount as unknown as number, { shouldValidate: true });
      if (result.date) setValue("date", result.date);
      if (result.category) {
        setValue("category", result.category, { shouldValidate: true });
        setValue("subcategory", result.subcategory ?? "");
      }
      setScannedText(result.raw_text);
      if (result.category && result.prediction_id !== null && result.confidence !== null) {
        setSuggestion({
          predictionId: result.prediction_id,
          category: result.category,
          subcategory: result.subcategory ?? "",
          confidence: result.confidence,
          needsReview: result.needs_review ?? false,
        });
      }
      if (!result.amount && !result.merchant && !result.category) {
        toast.error("Couldn't read enough from that receipt — please fill in the details manually.");
      }
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Couldn't scan that receipt.");
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

    // If the user changed the suggested category/subcategory before
    // submitting, that override is real signal about a wrong prediction —
    // record it as feedback rather than silently discarding it.
    if (
      suggestion &&
      (values.category !== suggestion.category || (values.subcategory || "") !== suggestion.subcategory)
    ) {
      api
        .submitFeedback({
          prediction_id: suggestion.predictionId,
          feedback_type: "category_correction",
          corrected_value: values.subcategory ? `${values.category} > ${values.subcategory}` : values.category,
        })
        .catch(() => {
          /* best-effort — a failed feedback write shouldn't block the transaction that already saved */
        });
    }
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

      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">
          Have a merchant or description? Get a suggested category from the trained model.
        </p>
        <div className="flex shrink-0 gap-2">
          <input
            ref={receiptInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) scanReceipt.mutate(file);
              e.target.value = "";
            }}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            isLoading={scanReceipt.isPending}
            onClick={() => receiptInputRef.current?.click()}
          >
            <Camera />
            Scan receipt
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            isLoading={categorize.isPending}
            onClick={() => categorize.mutate()}
          >
            <Sparkles />
            Suggest category
          </Button>
        </div>
      </div>

      {scannedText && (
        <details className="rounded-md border border-border p-2 text-xs text-muted-foreground">
          <summary className="cursor-pointer select-none">Scanned text (OCR) — review before saving</summary>
          <pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap">{scannedText}</pre>
        </details>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="category">Category</Label>
            {suggestion && (
              <Badge variant={suggestion.needsReview ? "warning" : "outline"}>
                {suggestion.needsReview ? "Needs review — " : ""}
                {Math.round(suggestion.confidence * 100)}% confidence
              </Badge>
            )}
          </div>
          <Input id="category" placeholder="Groceries" {...register("category")} />
          {errors.category && <p className="text-xs text-danger">{errors.category.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="subcategory">Subcategory</Label>
          <Input id="subcategory" placeholder="Optional" {...register("subcategory")} />
        </div>
      </div>

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
