import { motion } from "framer-motion";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/components/ui/toaster";
import { api } from "@/lib/api";
import { CURRENCIES, USER_TYPES } from "@/lib/constants";

export function Onboarding() {
  const navigate = useNavigate();
  const [userType, setUserType] = useState("");
  const [monthlyIncome, setMonthlyIncome] = useState("");
  const [monthlyBudget, setMonthlyBudget] = useState("");
  const [currency, setCurrency] = useState("INR");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function saveProfile() {
    setIsSubmitting(true);
    try {
      await api.updateProfile({
        user_type: userType || undefined,
        monthly_income: monthlyIncome ? Number(monthlyIncome) : undefined,
        monthly_budget: monthlyBudget ? Number(monthlyBudget) : undefined,
        currency,
      });
      navigate("/dashboard");
    } catch {
      toast.error("Couldn't save your profile. You can update it later in Settings.");
      navigate("/dashboard");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-md space-y-6"
      >
        <div className="space-y-1 text-center">
          <h1 className="text-xl font-semibold tracking-tight">Tell us about yourself</h1>
          <p className="text-sm text-muted-foreground">
            This helps FinPilot personalize your dashboard. You can change it anytime.
          </p>
        </div>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>I am a</Label>
            <Select value={userType} onValueChange={setUserType}>
              <SelectTrigger>
                <SelectValue placeholder="Select your profile" />
              </SelectTrigger>
              <SelectContent>
                {USER_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type.replace("_", " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="income">Monthly income</Label>
              <Input
                id="income"
                type="number"
                placeholder="50000"
                value={monthlyIncome}
                onChange={(e) => setMonthlyIncome(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="budget">Monthly budget</Label>
              <Input
                id="budget"
                type="number"
                placeholder="40000"
                value={monthlyBudget}
                onChange={(e) => setMonthlyBudget(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Currency</Label>
            <Select value={currency} onValueChange={setCurrency}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CURRENCIES.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex gap-3">
          <Button variant="outline" className="flex-1" onClick={() => navigate("/dashboard")}>
            Skip for now
          </Button>
          <Button className="flex-1" onClick={saveProfile} isLoading={isSubmitting}>
            Continue
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
