"use client";

import { useRouter, usePathname } from "next/navigation";
import { Library, Menu, X, Activity, Database, Inbox, FileText, Workflow, ExternalLink, BookOpen, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useSidebar } from "./sidebar-provider";

type NavItem = "library" | "configs" | "events" | "docs" | "temporal" | "rabbitmq" | "database" | "api-docs";

export function Sidebar() {
  const { isOpen, setIsOpen } = useSidebar();
  const router = useRouter();
  const pathname = usePathname();

  const tabs: Array<{ id: NavItem; icon: any; label: string; path: string }> = [
    { id: "library", icon: Library, label: "Libraries", path: "/libraries" },
    { id: "configs", icon: Settings, label: "Vectorization Configs", path: "/configs" },
    { id: "events", icon: Activity, label: "Events", path: "/events" },
    { id: "docs", icon: BookOpen, label: "Docs", path: "/docs" },
  ];

  const infraLinks: Array<{ id: NavItem; icon: any; label: string; href: string }> = [
    {
      id: "temporal",
      icon: Workflow,
      label: "Temporal",
      href: process.env.NEXT_PUBLIC_TEMPORAL_UI_HOST || "http://localhost:8080"
    },
    {
      id: "rabbitmq",
      icon: Inbox,
      label: "RabbitMQ",
      href: process.env.NEXT_PUBLIC_RABBITMQ_UI_HOST || "http://localhost:15672"
    },
    {
      id: "database",
      icon: Database,
      label: "Postgres",
      href: process.env.NEXT_PUBLIC_DATABASE_UI_HOST || "http://localhost:8081"
    },
    {
      id: "api-docs",
      icon: FileText,
      label: "API Docs",
      href: process.env.NEXT_PUBLIC_API_DOCS_URL || "http://localhost:8000/docs"
    },
  ];

  return (
    <>
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-screen border-r bg-background shadow-sm transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "-translate-x-full",
          "w-64"
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header with Toggle */}
          <div className="flex items-center justify-between border-b p-4">
            <h2 className="text-lg font-semibold">StackAI</h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(false)}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Main Navigation */}
          <nav className="space-y-1 border-b p-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = pathname.startsWith(tab.path);

              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    router.push(tab.path);
                  }}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                    isActive
                      ? "bg-accent text-accent-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Infra Section */}
          <div className="flex-1 overflow-y-auto p-2">
            <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Infra
            </h3>
            <nav className="space-y-1">
              {infraLinks.map((link) => {
                const Icon = link.icon;

                return (
                  <a
                    key={link.id}
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                      "text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="flex-1">{link.label}</span>
                    <ExternalLink className="h-3 w-3 opacity-50" />
                  </a>
                );
              })}
            </nav>
          </div>
        </div>
      </aside>

      {/* Toggle Button - Only visible when sidebar is closed */}
      {!isOpen && (
        <Button
          variant="outline"
          size="icon"
          onClick={() => setIsOpen(true)}
          className="fixed left-4 top-4 z-50 shadow-lg"
        >
          <Menu className="h-4 w-4" />
        </Button>
      )}

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
