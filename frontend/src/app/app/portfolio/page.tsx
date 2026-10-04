"use client";

import React from "react";
import { PortfolioOverview } from "@/components/PortfolioOverview";
import { useRefresh } from "@/lib/refresh-context";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";

export default function PortfolioPage() {
  const { refreshKey } = useRefresh();
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/app"
              className="text-xs text-fg-subtle hover:text-fg transition-colors flex items-center gap-1 font-mono"
            >
              <ArrowLeft className="h-3 w-3" />
              <span>Overview</span>
            </Link>
            <span className="text-fg-subtle text-xs">/</span>
            <span className="text-xs font-mono text-accent">Holdings</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
            Portfolio & Asset Holdings
          </h1>
          <p className="text-xs text-fg-subtle mt-0.5">
            Settled balances, asset exposure distribution, and real-time market valuations
          </p>
        </div>

        <div>
          <Link
            href="/app"
            className="rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white shadow-subtle hover:bg-accent-dark transition-all flex items-center gap-1.5"
          >
            <span>Trade Desk</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      <PortfolioOverview refreshTrigger={refreshKey} />
    </div>
  );
}
