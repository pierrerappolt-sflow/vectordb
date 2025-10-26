"use client";

import { useState } from "react";
import { Library, FileText, Settings, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useSidebar } from "./sidebar-provider";

type TabType = "library" | "docs" | "settings";

interface SidebarProps {
  children?: React.ReactNode;
}

export function Sidebar({ children }: SidebarProps) {
  const [activeTab, setActiveTab] = useState<TabType>("library");
  const { isOpen, setIsOpen } = useSidebar();

  const tabs = [
    { id: "library" as TabType, icon: Library, label: "Library" },
    { id: "docs" as TabType, icon: FileText, label: "Docs" },
    { id: "settings" as TabType, icon: Settings, label: "Settings" },
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

          {/* Tabs */}
          <nav className="space-y-1 border-b p-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
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

          {/* Tab Content */}
          <div className="flex-1 overflow-auto p-4">
            {activeTab === "library" && (
              <div>
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Your Libraries
                </h3>
                {children}
              </div>
            )}
            {activeTab === "docs" && (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <FileText className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Documentation coming soon
                  </p>
                </div>
              </div>
            )}
            {activeTab === "settings" && (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <Settings className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Settings coming soon
                  </p>
                </div>
              </div>
            )}
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
