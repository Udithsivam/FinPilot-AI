import { Toaster as Sonner } from "sonner";

import { useTheme } from "@/hooks/use-theme";

export function Toaster() {
  const { theme } = useTheme();
  return (
    <Sonner
      theme={theme}
      position="top-right"
      toastOptions={{
        classNames: {
          toast:
            "bg-card! text-card-foreground! border! border-border! shadow-lg! rounded-lg!",
          description: "text-muted-foreground!",
        },
      }}
    />
  );
}

export { toast } from "sonner";
