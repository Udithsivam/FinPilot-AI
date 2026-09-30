import { Menu, Moon, Rocket, Sun } from "lucide-react";
import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useTheme } from "@/hooks/use-theme";
import { NAV_ITEMS } from "@/lib/nav";
import { cn } from "@/lib/utils";

function currentTitle(pathname: string) {
  const match = NAV_ITEMS.find((item) => pathname.startsWith(item.to));
  return match?.label ?? "FinPilot AI";
}

export function TopHeader() {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-card/80 px-4 backdrop-blur-sm md:px-6">
      <div className="flex items-center gap-2 md:hidden">
        <div className="flex size-7 items-center justify-center rounded-md bg-brand text-brand-foreground">
          <Rocket className="size-3.5" />
        </div>
        <span className="text-sm font-semibold">FinPilot AI</span>
      </div>

      <h1 className="hidden text-lg font-semibold tracking-tight md:block">
        {currentTitle(location.pathname)}
      </h1>

      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </Button>
        <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMenuOpen(true)}>
          <Menu className="size-4" />
        </Button>
      </div>

      <Dialog open={menuOpen} onOpenChange={setMenuOpen}>
        <DialogContent className="top-0 mt-0 max-w-none translate-y-0 rounded-none border-0 p-6 sm:top-1/2 sm:mt-0 sm:max-w-sm sm:-translate-y-1/2 sm:rounded-xl sm:border">
          <DialogTitle>Menu</DialogTitle>
          <nav className="mt-2 flex flex-col gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium",
                    isActive
                      ? "bg-brand-subtle text-brand-subtle-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )
                }
              >
                <item.icon className="size-4" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </DialogContent>
      </Dialog>
    </header>
  );
}
