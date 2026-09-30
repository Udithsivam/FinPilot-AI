import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AIInsights } from "@/pages/AIInsights";
import { Analytics } from "@/pages/Analytics";
import { Budgets } from "@/pages/Budgets";
import { Dashboard } from "@/pages/Dashboard";
import { Goals } from "@/pages/Goals";
import { Landing } from "@/pages/Landing";
import { Login } from "@/pages/Login";
import { MLOps } from "@/pages/MLOps";
import { Onboarding } from "@/pages/Onboarding";
import { Predictions } from "@/pages/Predictions";
import { Register } from "@/pages/Register";
import { Settings } from "@/pages/Settings";
import { Transactions } from "@/pages/Transactions";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/transactions" element={<Transactions />} />
        <Route path="/budgets" element={<Budgets />} />
        <Route path="/goals" element={<Goals />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/insights" element={<AIInsights />} />
        <Route path="/predictions" element={<Predictions />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/mlops" element={<MLOps />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
