import { NavLink } from "react-router-dom";

import { MOBILE_NAV_ITEMS } from "@/lib/nav";
import { cn } from "@/lib/utils";

export function MobileBottomNav() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 flex h-16 items-center justify-around border-t border-border bg-card/95 backdrop-blur-sm md:hidden">
      {MOBILE_NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            cn(
              "flex flex-1 flex-col items-center justify-center gap-0.5 py-2 text-[11px] font-medium",
              isActive ? "text-brand" : "text-muted-foreground",
            )
          }
        >
          <item.icon className="size-5" />
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
