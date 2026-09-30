import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const TONE_BG = {
  ai: "bg-ai-subtle text-ai-subtle-foreground",
  success: "bg-success-subtle text-success-subtle-foreground",
  warning: "bg-warning-subtle text-warning-subtle-foreground",
  danger: "bg-danger-subtle text-danger-subtle-foreground",
} as const;

interface AIInsightCardProps {
  title: string;
  description: string;
  tone?: keyof typeof TONE_BG;
  /** Shows a "Sample" badge — true by default since no live insight engine exists yet. */
  sample?: boolean;
  className?: string;
}

export function AIInsightCard({ title, description, tone = "ai", sample = true, className }: AIInsightCardProps) {
  return (
    <Card className={cn(className)}>
      <CardContent className="flex gap-3 p-4">
        <div className={cn("flex size-9 shrink-0 items-center justify-center rounded-lg", TONE_BG[tone])}>
          <Sparkles className="size-4" />
        </div>
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium">{title}</p>
            {sample && (
              <Badge variant="outline" className="shrink-0">
                Sample
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}
