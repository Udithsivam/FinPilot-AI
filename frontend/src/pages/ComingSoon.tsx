import type { LucideIcon } from "lucide-react";

import { PageContainer } from "@/components/layout/PageContainer";
import { EmptyState } from "@/components/ui/empty-state";

interface ComingSoonProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export function ComingSoon({ icon, title, description }: ComingSoonProps) {
  return (
    <PageContainer>
      <EmptyState icon={icon} title={title} description={description} className="min-h-[60vh]" />
    </PageContainer>
  );
}
