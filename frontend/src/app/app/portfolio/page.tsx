"use client";

import React from "react";
import { PortfolioOverview } from "@/components/PortfolioOverview";
import { useRefresh } from "@/lib/refresh-context";

export default function PortfolioPage() {
  const { refreshKey } = useRefresh();
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
          Portfolio & Holdings
        </h1>
        <p className="text-xs text-fg-subtle mt-1">
          Settled balances, asset exposure distribution, and real-time market valuations
        </p>
      </div>

      <PortfolioOverview refreshTrigger={refreshKey} />
    </div>
  );
}
