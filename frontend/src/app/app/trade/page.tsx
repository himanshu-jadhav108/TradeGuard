"use client";

import React, { useState } from "react";
import { TradeComposer } from "@/components/TradeComposer";
import { TradeReviewCard } from "@/components/TradeReviewCard";
import { TradeProposal, OrderRecord } from "@/lib/types";
import { useRefresh } from "@/lib/refresh-context";
import { ShieldCheck, FileCheck2, Lock, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function TradePage() {
  const [proposal, setProposal] = useState<TradeProposal | null>(null);
  const { triggerRefresh } = useRefresh();

  const handleConfirmed = (order: OrderRecord) => {
    triggerRefresh();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header with back navigation link */}
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
            <span className="text-xs font-mono text-accent">Trade Desk</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
            Trade Execution & Review Desk
          </h1>
          <p className="text-xs text-fg-subtle mt-0.5">
            Natural language parsing → Deterministic risk verification → Explicit human confirmation
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-full border border-border bg-canvas-subtle px-3 py-1 text-xs">
            <Lock className="h-3 w-3 text-accent" />
            <span className="font-mono text-[11px] font-medium text-fg-muted">
              Execution Boundary Enforced
            </span>
          </div>
        </div>
      </div>

      {/* Institutional Safety Banner */}
      <div className="flex items-start gap-3 rounded-2xl border border-border bg-canvas-subtle p-4 text-xs">
        <ShieldCheck className="h-4 w-4 text-accent shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-fg block text-[11px]">
            Server-Enforced Guardrail Invariant
          </span>
          <p className="text-fg-muted leading-relaxed text-[11px]">
            Every proposal is evaluated against your live USDC cash balance, the authorized asset allowlist, the $25,000 maximum order ceiling, and the 40% concentration threshold. Orders with a <span className="font-mono text-danger font-bold">BLOCK</span> status cannot be submitted or executed under any circumstances.
          </p>
        </div>
      </div>

      {/* Main Trade Composer */}
      <div className="space-y-6">
        <TradeComposer onProposalCreated={(p) => setProposal(p)} />

        {proposal ? (
          <div className="pt-2">
            <TradeReviewCard
              proposal={proposal}
              onTradeConfirmed={handleConfirmed}
              onCancelled={() => setProposal(null)}
            />
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-border bg-surface/50 p-8 text-center text-fg-subtle flex flex-col items-center justify-center min-h-[220px]">
            <FileCheck2 className="h-6 w-6 text-accent mb-2" />
            <h3 className="text-xs font-semibold text-fg">
              Awaiting Proposal Parameters
            </h3>
            <p className="text-[11px] text-fg-subtle max-w-sm mt-1">
              Select one of the 1-click test scenarios above or type an intent to view the live quote snapshot and risk engine verification card.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
