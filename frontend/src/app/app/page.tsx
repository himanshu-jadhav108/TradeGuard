"use client";

import React, { useState } from "react";
import { TradeComposer } from "@/components/TradeComposer";
import { TradeReviewCard } from "@/components/TradeReviewCard";
import { PortfolioOverview } from "@/components/PortfolioOverview";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { TradeProposal, OrderRecord } from "@/lib/types";
import { useRefresh } from "@/lib/refresh-context";
import Link from "next/link";
import { ArrowRight, Terminal } from "lucide-react";

export default function OverviewPage() {
  const { refreshKey, triggerRefresh } = useRefresh();
  const [activeProposal, setActiveProposal] = useState<TradeProposal | null>(
    null
  );

  const handleOrderConfirmed = (order: OrderRecord) => {
    triggerRefresh();
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
            Overview Dashboard
          </h1>
          <p className="text-xs text-fg-subtle mt-1 font-mono">
            Settled positions · Deterministic risk execution · Real-time audit
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/app/trade"
            className="rounded-xl bg-accent px-4 py-2.5 text-xs font-semibold text-white shadow-subtle hover:bg-accent-dark transition-all flex items-center gap-1.5"
          >
            <span>Open Dedicated Trade Desk</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Portfolio Metrics & Allocation Charts */}
      <PortfolioOverview refreshTrigger={refreshKey} />

      {/* Active Trade Review or Intent Execution Section */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-fg uppercase tracking-wider font-mono">
            Pre-Trade Review Desk
          </h2>
          <span className="text-[11px] font-mono text-fg-subtle">
            Instant Intent Testing
          </span>
        </div>

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
              <div className="rounded-2xl border border-dashed border-border bg-surface/50 p-8 sm:p-12 text-center text-fg-subtle flex flex-col items-center justify-center min-h-[320px] shadow-subtle">
                <div className="h-10 w-10 rounded-xl bg-canvas-subtle border border-border flex items-center justify-center mb-3 text-fg-muted">
                  <Terminal className="h-5 w-5 text-accent" />
                </div>
                <h3 className="text-sm font-semibold text-fg">
                  Ready for Trade Intent
                </h3>
                <p className="text-xs text-fg-subtle max-w-sm mt-1 leading-relaxed">
                  Enter an intent like “Buy $500 of BTC” in the composer on the left to evaluate proposal parameters and deterministic risk checks.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="space-y-3 pt-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-fg uppercase tracking-wider font-mono">
            Recent Audit Stream
          </h2>
          <Link
            href="/app/activity"
            className="text-xs font-semibold text-accent hover:text-accent-dark transition-colors flex items-center gap-1"
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
