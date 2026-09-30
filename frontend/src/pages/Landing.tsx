import { motion } from "framer-motion";
import { BarChart3, HeartPulse, Rocket, Sparkles, Target, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const FEATURES = [
  {
    icon: HeartPulse,
    title: "Financial Health Score",
    description: "An explainable score built from your own spending, budgets and goals — not a black box.",
  },
  {
    icon: TrendingUp,
    title: "Savings prediction",
    description: "A trained model estimates your desired savings from your income and expense profile.",
  },
  {
    icon: BarChart3,
    title: "Real analytics",
    description: "Cash flow, category breakdowns and budget tracking, computed from your own transactions.",
  },
  {
    icon: Target,
    title: "Goals that connect to spending",
    description: "Track progress toward what you're actually saving for, not just abstract totals.",
  },
];

export function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-brand text-brand-foreground">
            <Rocket className="size-4" />
          </div>
          <span className="text-base font-semibold tracking-tight">FinPilot AI</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" asChild>
            <Link to="/login">Sign in</Link>
          </Button>
          <Button asChild>
            <Link to="/register">Get started</Link>
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6">
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex flex-col items-center gap-6 py-20 text-center"
        >
          <div className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            <Sparkles className="size-3.5 text-ai" />
            AI-powered financial intelligence
          </div>
          <h1 className="max-w-2xl text-4xl font-bold tracking-tight sm:text-5xl">
            Understand your money, not just track it.
          </h1>
          <p className="max-w-xl text-lg text-muted-foreground">
            FinPilot AI turns your transactions into a real financial health score, savings predictions and
            explainable analytics — built on a production ML pipeline, not guesswork.
          </p>
          <div className="flex gap-3">
            <Button size="lg" asChild>
              <Link to="/register">Create your account</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/login">Sign in</Link>
            </Button>
          </div>
        </motion.section>

        <section className="grid grid-cols-1 gap-4 pb-24 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <Card className="h-full">
                <CardContent className="space-y-3 p-5">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-brand-subtle">
                    <feature.icon className="size-5 text-brand-subtle-foreground" />
                  </div>
                  <p className="font-medium">{feature.title}</p>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </section>
      </main>
    </div>
  );
}
