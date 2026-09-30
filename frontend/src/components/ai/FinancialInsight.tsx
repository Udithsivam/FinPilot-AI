import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";

interface FinancialInsightProps {
  text: string;
  /** No live insight-generation engine yet — defaults true. */
  sample?: boolean;
}

export function FinancialInsight({ text, sample = true }: FinancialInsightProps) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-ai-subtle bg-ai-subtle/40 p-4">
      <Sparkles className="mt-0.5 size-4 shrink-0 text-ai" />
      <p className="flex-1 text-sm text-foreground">{text}</p>
      {sample && (
        <Badge variant="outline" className="shrink-0">
          Sample
        </Badge>
      )}
    </div>
  );
}
