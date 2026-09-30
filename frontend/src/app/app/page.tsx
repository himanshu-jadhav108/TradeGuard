"use client";

import React, { useState } from "react";
import { TradeComposer } from "@/components/TradeComposer";
import { TradeReviewCard } from "@/components/TradeReviewCard";
import { PortfolioOverview } from "@/components/PortfolioOverview";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { TradeProposal, OrderRecord } from "@/lib/types";
import { useRefresh } from "@/lib/refresh-context";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

export default function OverviewPage() {
  const { refreshKey, triggerRefresh } = useRefresh();
  const [activeProposal, setActiveProposal] = useState<TradeProposal | null>(
    null
  );

  const handleOrderConfirmed = (order: OrderRecord) => {
    triggerRefresh();
  };

  return (
    <div className="space-y-10">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
            Overview Dashboard
          </h1>
          <p className="text-xs text-fg-subtle mt-1">
            Real-time portfolio metrics, intent execution, and risk controls
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/app/trade"
            className="rounded-xl bg-emerald px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-dark transition-all flex items-center gap-1.5"
          >
            <span>Open Trade Composer</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Portfolio Metrics & Allocation Charts */}
      <PortfolioOverview refreshTrigger={refreshKey} />

      {/* Active Trade Review or Intent Execution Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-5 space-y-4">
          <TradeComposer
            onProposalCreated={(prop) => setActiveProposal(prop)}
          />
        </div>

        <div className="lg:col-span-7">
          {activeProposal ? (
            <TradeReviewCard
              proposal={activeProposal}
              onTradeConfirmed={handleOrderConfirmed}
              onCancelled={() => setActiveProposal(null)}
            />
          ) : (
            <div className="rounded-2xl border border-dashed border-border bg-surface/50 p-8 text-center text-fg-subtle flex flex-col items-center justify-center min-h-[300px]">
              <Sparkles className="h-8 w-8 text-emerald mb-2" />
              <h3 className="text-sm font-semibold text-fg">
                Ready for Trade Intent
              </h3>
              <p className="text-xs text-fg-subtle max-w-xs mt-1">
                Enter a request like “Buy $500 of BTC” in the composer on the left to review proposal and deterministic risk checks.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-fg">Recent Audit Trail</h2>
          <Link
            href="/app/activity"
            className="text-xs font-semibold text-emerald hover:text-emerald-dark transition-colors flex items-center gap-1"
          >
            <span>View Full Audit Log</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        <ActivityTimeline refreshTrigger={refreshKey} />
      </div>
    </div>
  );
}
