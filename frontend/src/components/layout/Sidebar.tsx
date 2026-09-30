import { LogOut, PanelLeftClose, PanelLeftOpen, Rocket } from "lucide-react";
import { NavLink } from "react-router-dom";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/hooks/use-auth";
import { useSidebar } from "@/hooks/use-sidebar";
import { NAV_ITEMS } from "@/lib/nav";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const { user, logout } = useAuth();
  const { collapsed, toggle } = useSidebar();
  const initials = user?.full_name
    ?.split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <aside
      className={cn(
        "hidden shrink-0 flex-col border-r border-border bg-card transition-[width] duration-200 md:flex",
        collapsed ? "w-[72px]" : "w-64",
      )}
    >
      <div className="flex h-16 items-center gap-2 px-4">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand text-brand-foreground">
          <Rocket className="size-4" />
        </div>
        {!collapsed && <span className="truncate text-base font-semibold tracking-tight">FinPilot AI</span>}
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                collapsed && "justify-center px-0",
                isActive
                  ? "bg-brand-subtle text-brand-subtle-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )
            }
          >
            <item.icon className="size-4 shrink-0" />
            {!collapsed && <span className="truncate">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <button
        onClick={toggle}
        className={cn(
          "mx-3 mb-2 flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground",
          "transition-colors hover:bg-muted hover:text-foreground",
          collapsed && "justify-center px-0",
        )}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
        {!collapsed && "Collapse"}
      </button>

      <div className={cn("flex items-center gap-3 border-t border-border p-4", collapsed && "justify-center px-2")}>
        <Avatar>
          <AvatarFallback>{initials ?? "?"}</AvatarFallback>
        </Avatar>
        {!collapsed && (
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{user?.full_name}</p>
            <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
          </div>
        )}
        <button
          onClick={logout}
          className="shrink-0 rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label="Log out"
        >
          <LogOut className="size-4" />
        </button>
      </div>
    </aside>
  );
}
