"use client";

import { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Breadcrumbs } from "./breadcrumbs";
import { Button } from "./button";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  breadcrumbs?: BreadcrumbItem[];
  title: string;
  description?: string;
  actions?: ReactNode;
}

export function PageHeader({ breadcrumbs, title, description, actions }: PageHeaderProps) {
  const router = useRouter();
  const hasParent = breadcrumbs && breadcrumbs.length > 1;
  const parentHref = hasParent ? breadcrumbs[breadcrumbs.length - 2].href : null;

  return (
    <div className="space-y-6">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumbs items={breadcrumbs} />
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          {hasParent && parentHref && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push(parentHref)}
              className="mt-1"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
          )}
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
            {description && (
              <p className="text-muted-foreground">{description}</p>
            )}
          </div>
        </div>

        {actions && (
          <div className="flex items-center gap-2">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}
