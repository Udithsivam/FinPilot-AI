import { useQuery } from "@tanstack/react-query";
import { Activity, Database, GitBranch, MessageSquareWarning, ShieldOff } from "lucide-react";

import { PageContainer } from "@/components/layout/PageContainer";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, api } from "@/lib/api";

const STAGE_VARIANT: Record<string, "outline" | "success" | "warning" | "brand"> = {
  candidate: "outline",
  validated: "warning",
  production: "success",
  archived: "outline",
};

export function MLOps() {
  const summary = useQuery({ queryKey: ["mlops-summary"], queryFn: api.mlopsSummary, retry: false });

  if (summary.isLoading) {
    return (
      <PageContainer className="space-y-4">
        <Skeleton className="h-24" />
        <Skeleton className="h-64" />
      </PageContainer>
    );
  }

  if (summary.isError) {
    const forbidden = summary.error instanceof ApiError && summary.error.status === 403;
    return (
      <PageContainer>
        <EmptyState
          icon={ShieldOff}
          title={forbidden ? "Admin access required" : "Couldn't load MLOps dashboard"}
          description={
            forbidden
              ? "This internal dashboard is restricted to accounts listed in the ADMIN_EMAILS environment variable."
              : "Something went wrong loading MLOps data."
          }
        />
      </PageContainer>
    );
  }

  const data = summary.data!;

  return (
    <PageContainer className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">MLOps Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Internal view of the model registry, monitoring, drift, feedback and RAG pipeline — real data only.
        </p>
      </div>

      <section className="space-y-3">
        <h3 className="flex items-center gap-2 text-base font-semibold">
          <GitBranch className="size-4" /> Model registry
        </h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {Object.entries(data.registry).map(([name, versions]) => (
            <Card key={name}>
              <CardHeader>
                <CardTitle className="text-sm font-medium">{name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {(versions as any[]).length === 0 ? (
                  <p className="text-sm text-muted-foreground">No versions registered.</p>
                ) : (
                  (versions as any[]).map((v) => (
                    <div key={v.version} className="flex items-center justify-between text-sm">
                      <span>v{v.version}</span>
                      <Badge variant={STAGE_VARIANT[v.lifecycle_stage] ?? "outline"} className="capitalize">
                        {v.lifecycle_stage}
                      </Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h3 className="flex items-center gap-2 text-base font-semibold">
          <Activity className="size-4" /> Prediction performance
        </h3>
        <Card>
          <CardContent className="divide-y divide-border p-0">
            {data.performance.map((row: any, i: number) => (
              <div key={i} className="flex items-center justify-between gap-3 p-4">
                <div>
                  <p className="text-sm font-medium capitalize">{row.prediction_type.replace(/_/g, " ")}</p>
                  <p className="text-xs text-muted-foreground">
                    {row.model_name ? `${row.model_name} (v${row.model_version})` : "No model yet"}
                  </p>
                </div>
                {row.status === "insufficient_data" ? (
                  <Badge variant="outline">insufficient data</Badge>
                ) : (
                  <div className="text-right text-xs text-muted-foreground">
                    <p>MAE {row.mae?.toFixed(2)}</p>
                    <p>RMSE {row.rmse?.toFixed(2)}</p>
                    <p>R² {row.r2 !== null ? row.r2.toFixed(3) : "n/a"}</p>
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="space-y-3">
        <h3 className="flex items-center gap-2 text-base font-semibold">
          <MessageSquareWarning className="size-4" /> Drift monitoring
        </h3>
        <Card>
          <CardContent className="divide-y divide-border p-0">
            {data.drift.map((row: any, i: number) => (
              <div key={i} className="flex items-center justify-between gap-3 p-4">
                <div>
                  <p className="text-sm font-medium">{row.feature}</p>
                  <p className="text-xs text-muted-foreground">
                    {row.metric} · reference n={row.reference_size}, current n={row.current_size}
                  </p>
                </div>
                <Badge
                  variant={
                    row.status === "drift_detected" ? "danger" : row.status === "warning" ? "warning" : "outline"
                  }
                >
                  {row.status.replace(/_/g, " ")}
                  {row.value !== null ? ` (${row.value})` : ""}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Feedback</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <p>Total feedback: {data.feedback.total_feedback}</p>
            <p>Category corrections: {data.feedback.category_corrections}</p>
            <p className="text-xs text-muted-foreground">{data.feedback.note}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Database className="size-4" /> RAG knowledge base
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <p>Documents: {data.rag.document_count}</p>
            <p>Chunks: {data.rag.chunk_count}</p>
            <p className="text-xs text-muted-foreground">{data.rag.embedding_method}</p>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  );
}
