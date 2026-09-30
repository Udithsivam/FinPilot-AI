# FinPilot AI — Frontend

React + TypeScript + Vite frontend for FinPilot AI.

## Stack

TypeScript, React, Vite, Tailwind CSS v4, Radix UI primitives (styled
in the shadcn/ui pattern), Lucide icons, Recharts, Framer Motion,
React Hook Form + Zod, TanStack Query, React Router.

## Running it

```
npm install
npm run dev
```

The dev server proxies `/api/*` to `http://127.0.0.1:8000` (see
`vite.config.ts`), so run the FastAPI backend alongside it:

```
# from the repo root
uvicorn backend.app.main:app --reload
```

Then open http://localhost:5173.

```
npm run build   # production build (tsc -b && vite build)
npm run lint    # oxlint
```

## Design system

All color/spacing/radius/shadow tokens live in `src/index.css` as CSS
custom properties (`:root` for light, `.dark` for dark mode, mapped
into Tailwind's `@theme`). Never hardcode a color in a component —
always use the semantic Tailwind utility (`bg-brand`, `text-muted-foreground`,
`bg-danger-subtle`, etc.) so both themes and future palette tweaks stay
in one place.

- **Brand** (`brand`/`brand-hover`): primary green, used for the core
  app's primary actions and financial data.
- **AI accent** (`ai`): a distinct violet, used only in `components/ai/*`
  so AI-generated content is visually distinguishable from real,
  data-driven UI.
- **Semantic**: `success`/`warning`/`danger`/`info`, each with a
  `-subtle`/`-subtle-foreground` pair for badges and tinted backgrounds.
- **Typography scale**: `text-display`, `text-page-heading`,
  `text-section-heading`, `text-card-heading`, `text-body`,
  `text-small`, `text-tiny` (size + line-height baked in; apply
  `font-bold`/`font-semibold`/etc. separately).
- Dark mode is class-based (`.dark` on `<html>`), toggled via
  `useTheme()` (`src/hooks/use-theme.tsx`) and persisted to
  `localStorage`. An inline script in `index.html` applies it before
  first paint to avoid a flash of the wrong theme.
- `prefers-reduced-motion` is respected globally (see the `@media`
  block in `index.css`).

## Structure

```
src/
  components/
    ui/          reusable primitives: Button, Input, Select, Dialog, Tabs,
                  Badge, Toaster, Skeleton, Progress, Avatar, EmptyState, ErrorState
    layout/       AppShell, Sidebar (collapsible, desktop/tablet), TopHeader,
                  MobileBottomNav, PageContainer
    financial/    MetricCard, FinancialHealthCard, BudgetCard, GoalCard,
                  TransactionRow, TransactionForm, SpendingBreakdown, CashFlowChart
    ai/           AIInsightCard, PredictionCard, PredictionExplanation,
                  RecommendationCard, AnomalyAlert, FinancialInsight
    auth/         ProtectedRoute
  hooks/          use-auth, use-theme, use-sidebar
  lib/            api.ts (typed fetch client), nav.ts, utils.ts
  mocks/          ai.ts — sample-only data for AI components (see below)
  pages/          Landing, Login, Register, Onboarding, Dashboard, ComingSoon
  types/          api.ts — TypeScript types mirroring the backend's Pydantic schemas
```

## Real data vs. sample data

Everything on the **Dashboard** is wired to the real FastAPI backend via
TanStack Query (`src/lib/api.ts`): income/expenses/net cash flow/savings
rate, the Financial Health Score, cash flow over time, category
spending, budgets and goals.

The **AI components** (`components/ai/*`) are built and ready, but the
backend doesn't yet implement categorization, forecasting, anomaly
detection, recommendations or explainability (Phase 5, paused). Using
any of them with real-looking numbers before those exist would present
fabricated ML output as real, so:

- Every AI component defaults its `sample` prop to `true` and renders
  a visible "Sample" badge.
- Sample content lives only in `src/mocks/ai.ts`, clearly commented,
  and is not imported by any production page (Dashboard, etc.).
- `PredictionCard` is the one exception — it takes a real
  `predicted_desired_savings` number from `POST /predict/savings`
  (already a real, trained-model endpoint) and defaults `sample` to
  `false`.

When Phase 5 intelligence features are built, wire their real API
responses into these same components and drop the `sample` prop (or
set it to `false`) — don't build new components for it.

## Pages

All 11 pages are built and wired to the real backend: Landing, Login,
Register, Onboarding, Dashboard, Transactions, Budgets, Goals,
Analytics, AI Insights, Predictions, Settings. `ComingSoon` (in
`pages/ComingSoon.tsx`) remains available as a reusable placeholder for
any future page, but nothing currently routes to it.
