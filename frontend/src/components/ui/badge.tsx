import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
  {
    variants: {
      variant: {
        default: "bg-muted text-muted-foreground",
        brand: "bg-brand-subtle text-brand-subtle-foreground",
        success: "bg-success-subtle text-success-subtle-foreground",
        warning: "bg-warning-subtle text-warning-subtle-foreground",
        danger: "bg-danger-subtle text-danger-subtle-foreground",
        outline: "border border-border text-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
