"use client";

import React, { useState, useRef } from "react";
import { TradeComposer } from "@/components/TradeComposer";
import { TradeReviewCard } from "@/components/TradeReviewCard";
import { MarketContextChart } from "@/components/MarketContextChart";
import { PortfolioContextStrip } from "@/components/PortfolioContextStrip";
import { RecentActivityPreview } from "@/components/RecentActivityPreview";
import { TradeProposal, OrderRecord } from "@/lib/types";
import { useRefresh } from "@/lib/refresh-context";
import { Shield, Lock, Terminal, BarChart2, CheckCircle2, ArrowRight } from "lucide-react";

export default function TradeDeskPage() {
  const { refreshKey, triggerRefresh } = useRefresh();
  const [activeProposal, setActiveProposal] = useState<TradeProposal | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<string>("BTC");

  // Mobile segmented view state: "composer" | "chart" | "review"
  const [mobileTab, setMobileTab] = useState<"composer" | "chart" | "review">("composer");

  // Desktop view mode state: "split" (both) | "review" | "chart"
  const [desktopMode, setDesktopMode] = useState<"split" | "review" | "chart">("split");

  const reviewSectionRef = useRef<HTMLDivElement>(null);

  const handleOrderConfirmed = (order: OrderRecord) => {
    triggerRefresh();
  };

  const handleProposalCreated = (prop: TradeProposal) => {
    setActiveProposal(prop);
    setSelectedAsset(prop.asset);
    // On mobile, immediately switch to the Review tab so the user sees the safety validation without scrolling
    setMobileTab("review");

    // On desktop, if in chart mode, switch to review or scroll to it
    if (desktopMode === "chart") {
      setDesktopMode("review");
    } else {
      setTimeout(() => {
        reviewSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    }
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
        {/* Desk Header with Mode Selectors */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-accent" />
            <h2 className="text-xs font-semibold text-fg uppercase tracking-wider font-mono">
              Pre-Trade Intelligence & Review Desk
            </h2>
          </div>

          {/* Desktop Mode Switcher (visible on lg+) */}
          <div className="hidden lg:flex items-center gap-1 p-1 bg-surface rounded-xl border border-border text-xs font-mono">
            <button
              onClick={() => setDesktopMode("split")}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                desktopMode === "split"
                  ? "bg-accent/15 text-accent border border-accent/30 font-semibold shadow-subtle"
                  : "text-fg-muted hover:text-fg"
              }`}
            >
              ⚡ Unified Stack
            </button>
            <button
              onClick={() => setDesktopMode("review")}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                desktopMode === "review"
                  ? "bg-accent/15 text-accent border border-accent/30 font-semibold shadow-subtle"
                  : "text-fg-muted hover:text-fg"
              }`}
            >
              <span>🛡️ Decision Review</span>
              {activeProposal && (
                <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
              )}
            </button>
            <button
              onClick={() => setDesktopMode("chart")}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                desktopMode === "chart"
                  ? "bg-accent/15 text-accent border border-accent/30 font-semibold shadow-subtle"
                  : "text-fg-muted hover:text-fg"
              }`}
            >
              📈 Market Chart
            </button>
          </div>
        </div>

        {/* Mobile Segmented View Switcher (visible below lg) */}
        <div className="lg:hidden flex items-center p-1 bg-surface rounded-xl border border-border shadow-subtle">
          <button
            onClick={() => setMobileTab("composer")}
            className={`flex-1 py-2 px-3 rounded-lg text-xs font-mono font-medium transition-all flex items-center justify-center gap-1.5 ${
              mobileTab === "composer"
                ? "bg-accent/15 text-accent border border-accent/30 font-bold shadow-subtle"
                : "text-fg-muted hover:text-fg"
            }`}
          >
            <Terminal className="h-3.5 w-3.5" />
            <span>Compose</span>
          </button>
          <button
            onClick={() => setMobileTab("chart")}
            className={`flex-1 py-2 px-3 rounded-lg text-xs font-mono font-medium transition-all flex items-center justify-center gap-1.5 ${
              mobileTab === "chart"
                ? "bg-accent/15 text-accent border border-accent/30 font-bold shadow-subtle"
                : "text-fg-muted hover:text-fg"
            }`}
          >
            <BarChart2 className="h-3.5 w-3.5" />
            <span>Chart</span>
          </button>
          <button
            onClick={() => setMobileTab("review")}
            className={`flex-1 py-2 px-3 rounded-lg text-xs font-mono font-medium transition-all flex items-center justify-center gap-1.5 ${
              mobileTab === "review"
                ? "bg-accent/15 text-accent border border-accent/30 font-bold shadow-subtle"
                : "text-fg-muted hover:text-fg"
            }`}
          >
            <Shield className="h-3.5 w-3.5" />
            <span>Review</span>
            {activeProposal && (
              <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
            )}
          </button>
        </div>

        {/* Mobile Quick-Jump Action Banner when proposal is active */}
        {activeProposal && (
          <div className="lg:hidden flex items-center justify-between p-2.5 rounded-xl bg-accent-surface border border-accent/30 text-xs font-mono">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-accent flex-shrink-0" />
              <span className="text-fg font-medium truncate">
                {activeProposal.side} {activeProposal.asset} proposed (${activeProposal.estimated_notional_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })})
              </span>
            </div>
            {mobileTab === "review" ? (
              <button
                onClick={() => setMobileTab("chart")}
                className="py-1 px-2.5 rounded-lg bg-surface border border-border text-accent font-semibold text-[11px] flex items-center gap-1"
              >
                <span>View Chart</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            ) : (
              <button
                onClick={() => setMobileTab("review")}
                className="py-1 px-2.5 rounded-lg bg-accent text-canvas font-bold text-[11px] flex items-center gap-1 shadow-subtle"
              >
                <span>Review Order</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            )}
          </div>
        )}

        {/* ========================================================
            DESKTOP LAYOUT (lg+): Sticky Composer + Intelligent Workspace
           ======================================================== */}
        <div className="hidden lg:grid lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Trade Composer (Sticky rail so user never loses demo scenarios) */}
          <div className="lg:col-span-4 space-y-4 sticky top-20 self-start">
            <TradeComposer onProposalCreated={handleProposalCreated} />
          </div>

          {/* Right Column: Controlled by Desktop Mode */}
          <div className="lg:col-span-8 space-y-6">
            {/* Show Chart if in 'split' or 'chart' mode */}
            {(desktopMode === "split" || desktopMode === "chart") && (
              <MarketContextChart
                initialAsset={selectedAsset}
                activeProposal={activeProposal}
                onSelectAsset={(a) => setSelectedAsset(a)}
              />
            )}

            {/* Show Review Card if in 'split' or 'review' mode */}
            {(desktopMode === "split" || desktopMode === "review") && (
              <div ref={reviewSectionRef}>
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
            )}
          </div>
        </div>

        {/* ========================================================
            MOBILE / SMALL SCREEN LAYOUT (< lg): Focused Single View
           ======================================================== */}
        <div className="lg:hidden space-y-4">
          {mobileTab === "composer" && (
            <div className="space-y-4">
              <TradeComposer onProposalCreated={handleProposalCreated} />
            </div>
          )}

          {mobileTab === "chart" && (
            <div className="space-y-4">
              <MarketContextChart
                initialAsset={selectedAsset}
                activeProposal={activeProposal}
                onSelectAsset={(a) => setSelectedAsset(a)}
              />
            </div>
          )}

          {mobileTab === "review" && (
            <div className="space-y-4">
              {activeProposal ? (
                <TradeReviewCard
                  proposal={activeProposal}
                  onTradeConfirmed={handleOrderConfirmed}
                  onCancelled={() => {
                    setActiveProposal(null);
                    setMobileTab("composer");
                  }}
                  onRefreshQuote={(newProp) => {
                    setActiveProposal(newProp);
                    setSelectedAsset(newProp.asset);
                  }}
                />
              ) : (
                <div className="rounded-2xl border border-border bg-surface p-6 text-center space-y-3">
                  <Shield className="h-8 w-8 text-accent mx-auto" />
                  <h3 className="text-sm font-bold text-fg">No Active Proposal</h3>
                  <p className="text-xs text-fg-subtle">
                    Choose a sample scenario or enter an intent in the Composer to stage a trade for risk review.
                  </p>
                  <button
                    onClick={() => setMobileTab("composer")}
                    className="py-2 px-4 rounded-xl bg-accent text-canvas font-bold text-xs shadow-subtle"
                  >
                    Go to Composer
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 4. Tertiary: Compact Recent Activity Preview */}
      <div className="pt-2">
        <RecentActivityPreview refreshTrigger={refreshKey} />
      </div>
    </div>
  );
}
