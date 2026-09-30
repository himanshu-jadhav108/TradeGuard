"use client";

import React, { useState } from "react";
import { TradeComposer } from "@/components/TradeComposer";
import { TradeReviewCard } from "@/components/TradeReviewCard";
import { TradeProposal, OrderRecord } from "@/lib/types";
import { ShieldCheck, FileCheck, Info } from "lucide-react";

export default function TradePage() {
  const [proposal, setProposal] = useState<TradeProposal | null>(null);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
          Trade Execution & Review
        </h1>
        <p className="text-xs text-fg-subtle mt-1">
          AI intent parsing → Deterministic risk engine → Live quotes → Explicit human confirmation
        </p>
      </div>

      {/* Safety Notice Banner */}
      <div className="flex items-start gap-3 rounded-2xl border border-emerald/20 bg-emerald-surface p-4 text-xs">
        <ShieldCheck className="h-5 w-5 text-emerald shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-fg">
            Deterministic Guardrail Active
          </span>
          <p className="text-fg-muted leading-relaxed">
            Every trade proposal is validated against your real account balance, maximum position size limits, and portfolio concentration thresholds. Trades flagged with a <span className="font-mono text-danger font-bold">BLOCK</span> status can never be executed.
          </p>
        </div>
      </div>

      <div className="space-y-6">
        <TradeComposer onProposalCreated={(p) => setProposal(p)} />

        {proposal && (
          <div className="pt-2">
            <TradeReviewCard
              proposal={proposal}
              onCancelled={() => setProposal(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
