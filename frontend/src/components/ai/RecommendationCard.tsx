import { Lightbulb } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface RecommendationCardProps {
  title: string;
  detected: string;
  why: string;
  action: string;
  impact: string;
  /** Recommendation engine isn't implemented on the backend yet — defaults true. */
  sample?: boolean;
}

export function RecommendationCard({ title, detected, why, action, impact, sample = true }: RecommendationCardProps) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Lightbulb className="size-4 text-ai" />
          {title}
        </CardTitle>
        {sample && <Badge variant="outline">Sample</Badge>}
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p>
          <span className="font-medium text-foreground">Detected: </span>
          <span className="text-muted-foreground">{detected}</span>
        </p>
        <p>
          <span className="font-medium text-foreground">Why it matters: </span>
          <span className="text-muted-foreground">{why}</span>
        </p>
        <p>
          <span className="font-medium text-foreground">Suggested action: </span>
          <span className="text-muted-foreground">{action}</span>
        </p>
        <p>
          <span className="font-medium text-foreground">Potential impact: </span>
          <span className="text-muted-foreground">{impact}</span>
        </p>
      </CardContent>
    </Card>
  );
}
