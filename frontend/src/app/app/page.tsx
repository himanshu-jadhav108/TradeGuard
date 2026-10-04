"use client";

import React, { useState } from "react";
import { TradeComposer } from "@/components/TradeComposer";
import { TradeReviewCard } from "@/components/TradeReviewCard";
import { PortfolioOverview } from "@/components/PortfolioOverview";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { TradeProposal, OrderRecord } from "@/lib/types";
import { useRefresh } from "@/lib/refresh-context";
import Link from "next/link";
import { ArrowRight, Terminal, Shield, Lock } from "lucide-react";

export default function TradeDeskPage() {
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
            Trade Desk
          </h1>
          <p className="text-xs text-fg-subtle mt-1 font-mono">
            Natural language intent · Server-enforced safety guardrails · Explicit human confirmation
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-full border border-border bg-canvas-subtle px-3 py-1 text-xs">
            <Lock className="h-3 w-3 text-accent" />
            <span className="font-mono text-[11px] font-medium text-fg-muted">
              Pre-Trade Safety Layer Active
            </span>
          </div>
        </div>
      </div>

      {/* Portfolio Metrics & Allocation Breakdown */}
      <PortfolioOverview refreshTrigger={refreshKey} />

      {/* Pre-Trade Review Desk (Hero Interactive Workflow) */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-fg uppercase tracking-wider font-mono flex items-center gap-1.5">
            <Shield className="h-4 w-4 text-accent" />
            <span>Pre-Trade Review Desk</span>
          </h2>
          <span className="text-[11px] font-mono text-fg-subtle">
            AI interprets · Backend validates · User decides
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
                onRefreshQuote={(newProp) => setActiveProposal(newProp)}
              />
            ) : (
              <div className="rounded-2xl border border-dashed border-border bg-surface/50 p-8 sm:p-12 text-center text-fg-subtle flex flex-col items-center justify-center min-h-[360px] shadow-subtle">
                <div className="h-10 w-10 rounded-xl bg-canvas-subtle border border-border flex items-center justify-center mb-3 text-fg-muted">
                  <Terminal className="h-5 w-5 text-accent" />
                </div>
                <h3 className="text-sm font-semibold text-fg">
                  Ready for Trade Intent
                </h3>
                <p className="text-xs text-fg-subtle max-w-sm mt-1 leading-relaxed">
                  Enter an intent like “Buy $500 of SOL” or pick one of the test scenarios on the left to evaluate proposal parameters, TTL quote freshness, and deterministic risk checks.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity Log */}
      <div className="space-y-3 pt-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-fg uppercase tracking-wider font-mono">
            Recent Activity Log
          </h2>
          <Link
            href="/app/activity"
            className="text-xs font-semibold text-accent hover:text-accent-dark transition-colors flex items-center gap-1"
          >
            <span>View Full Log</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        <ActivityTimeline refreshTrigger={refreshKey} />
      </div>
    </div>
  );
}
