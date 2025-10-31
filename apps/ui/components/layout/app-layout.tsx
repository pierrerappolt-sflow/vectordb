"use client";

import { Sidebar } from "./sidebar";
import { SidebarProvider, useSidebar } from "./sidebar-provider";

function AppLayoutContent({ children }: { children: React.ReactNode }) {
  const { isOpen } = useSidebar();

  return (
    <>
      <Sidebar />
      <main
        className="min-h-screen transition-all duration-300 ease-in-out lg:ml-64"
        style={{
          marginLeft: isOpen ? "256px" : "0px",
        }}
      >
        {children}
      </main>
    </>
  );
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <AppLayoutContent>{children}</AppLayoutContent>
    </SidebarProvider>
  );
}
