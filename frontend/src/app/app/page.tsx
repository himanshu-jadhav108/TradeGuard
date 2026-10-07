"use client";

import React, { useState } from "react";
import { TradeComposer } from "@/components/TradeComposer";
import { TradeReviewCard } from "@/components/TradeReviewCard";
import { MarketContextChart } from "@/components/MarketContextChart";
import { PortfolioContextStrip } from "@/components/PortfolioContextStrip";
import { RecentActivityPreview } from "@/components/RecentActivityPreview";
import { TradeProposal, OrderRecord } from "@/lib/types";
import { useRefresh } from "@/lib/refresh-context";
import { Shield, Lock } from "lucide-react";

export default function TradeDeskPage() {
  const { refreshKey, triggerRefresh } = useRefresh();
  const [activeProposal, setActiveProposal] = useState<TradeProposal | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<string>("BTC");

  const handleOrderConfirmed = (order: OrderRecord) => {
    triggerRefresh();
  };

  return (
    <div className="space-y-6">
      {/* 1. Page Header with Safety Layer Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
            Trade Desk
          </h1>
          <p className="text-xs text-fg-subtle mt-0.5 font-mono">
            Turn natural-language intent into a reviewed order before execution
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

      {/* 2. Compact Portfolio Context Strip */}
      <PortfolioContextStrip refreshTrigger={refreshKey} />

      {/* 3. Hero Decision Surface: Market Context + Trade Composer + Trade Review */}
      <div className="space-y-4 pt-1">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold text-fg uppercase tracking-wider font-mono flex items-center gap-1.5">
            <Shield className="h-3.5 w-3.5 text-accent" />
            <span>Pre-Trade Intelligence & Review Desk</span>
          </h2>
          <span className="text-[11px] font-mono text-fg-subtle">
            Market Context · Structured intent · Backend validates · User decides
          </span>
        </div>

        {/* Responsive Grid Layout:
            On Mobile: Market Context -> Trade Composer -> Trade Review
            On Desktop: Left (Trade Composer), Right (Market Context + Trade Review)
        */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Trade Composer (order-2 on mobile, order-1 on desktop) */}
          <div className="order-2 lg:order-1 lg:col-span-4 space-y-4">
            <TradeComposer
              onProposalCreated={(prop) => {
                setActiveProposal(prop);
                setSelectedAsset(prop.asset);
              }}
            />
          </div>

          {/* Right Column: Market Context + Trade Review (order-1 on mobile, order-2 on desktop) */}
          <div className="order-1 lg:order-2 lg:col-span-8 space-y-6">
            {/* Market Context Real OHLC Candlestick Chart */}
            <MarketContextChart
              initialAsset={selectedAsset}
              activeProposal={activeProposal}
              onSelectAsset={(a) => setSelectedAsset(a)}
            />

            {/* Core Decision Surface: Trade Review or Staging Staging Card */}
            {activeProposal ? (
              <TradeReviewCard
                proposal={activeProposal}
                onTradeConfirmed={handleOrderConfirmed}
                onCancelled={() => setActiveProposal(null)}
                onRefreshQuote={(newProp) => {
                  setActiveProposal(newProp);
                  setSelectedAsset(newProp.asset);
                }}
              />
            ) : (
              <div className="rounded-2xl border border-border bg-surface/75 p-6 sm:p-8 shadow-card flex flex-col justify-between min-h-[380px] precision-rail">
                {/* Header Strip */}
                <div className="flex items-center justify-between pb-3 border-b border-border text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-accent/60" />
                    <span className="font-semibold text-fg uppercase tracking-wider text-[11px]">
                      Pre-Trade Safety Decision Desk
                    </span>
                  </div>
                  <span className="text-[10px] text-fg-subtle px-2 py-0.5 rounded bg-canvas-subtle border border-border">
                    Awaiting Intent
                  </span>
                </div>

                {/* Staging Body */}
                <div className="my-auto py-8 text-center max-w-md mx-auto space-y-4">
                  <div className="h-12 w-12 rounded-2xl bg-canvas-subtle border border-border flex items-center justify-center mx-auto text-accent shadow-subtle">
                    <Shield className="h-6 w-6 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-fg tracking-tight">
                      Ready for Trade Intent
                    </h3>
                    <p className="text-xs text-fg-subtle mt-1.5 leading-relaxed">
                      Enter an intent like “Buy $500 of SOL” or pick a test scenario on the left. TradeGuard will interpret intent, secure a fresh quote, execute deterministic risk rules, and stage a safety ticket for your explicit confirmation.
                    </p>
                  </div>

                  {/* 4-Step Pipeline Indicator */}
                  <div className="grid grid-cols-4 gap-2 pt-2 text-[10px] font-mono text-fg-subtle">
                    <div className="p-2 rounded-lg bg-canvas-subtle border border-border/80 text-center">
                      <span className="block font-bold text-fg-muted mb-0.5">01</span>
                      <span>Intent</span>
                    </div>
                    <div className="p-2 rounded-lg bg-canvas-subtle border border-border/80 text-center">
                      <span className="block font-bold text-fg-muted mb-0.5">02</span>
                      <span>Quote TTL</span>
                    </div>
                    <div className="p-2 rounded-lg bg-canvas-subtle border border-border/80 text-center">
                      <span className="block font-bold text-fg-muted mb-0.5">03</span>
                      <span>Risk Rules</span>
                    </div>
                    <div className="p-2 rounded-lg bg-canvas-subtle border border-border/80 text-center">
                      <span className="block font-bold text-fg-muted mb-0.5">04</span>
                      <span>Confirm</span>
                    </div>
                  </div>
                </div>

                {/* Footer Principle Strip */}
                <div className="pt-3 border-t border-border flex items-center justify-between text-[11px] font-mono text-fg-subtle">
                  <span>Non-bypassable deterministic verification</span>
                  <span className="text-accent font-medium">User holds final authority</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Tertiary: Compact Recent Activity Preview */}
      <div className="pt-2">
        <RecentActivityPreview refreshTrigger={refreshKey} />
      </div>
    </div>
  );
}
