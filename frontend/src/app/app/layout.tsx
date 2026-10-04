"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { RefreshProvider, useRefresh } from "@/lib/refresh-context";

function AppLayoutInner({ children }: { children: React.ReactNode }) {
  const { triggerRefresh } = useRefresh();
  const pathname = usePathname();
  const isTradeDesk = pathname === "/app";

  return (
    <div
      className={`min-h-screen bg-canvas text-fg transition-colors ${
        isTradeDesk ? "bg-grid-workspace" : "bg-grid-ambient"
      }`}
    >
      <Navbar onReset={triggerRefresh} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <RefreshProvider>
      <AppLayoutInner>{children}</AppLayoutInner>
    </RefreshProvider>
  );
}
