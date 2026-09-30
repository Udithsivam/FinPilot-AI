import {
  LayoutDashboard,
  Receipt,
  Wallet,
  Target,
  BarChart3,
  Sparkles,
  TrendingUp,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/transactions", label: "Transactions", icon: Receipt },
  { to: "/budgets", label: "Budgets", icon: Wallet },
  { to: "/goals", label: "Goals", icon: Target },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/insights", label: "AI Insights", icon: Sparkles },
  { to: "/predictions", label: "Predictions", icon: TrendingUp },
  { to: "/settings", label: "Settings", icon: Settings },
];

export const MOBILE_NAV_ITEMS: NavItem[] = [
  NAV_ITEMS[0],
  NAV_ITEMS[1],
  NAV_ITEMS[2],
  NAV_ITEMS[3],
  NAV_ITEMS[5],
];
