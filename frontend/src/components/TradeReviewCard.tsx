"use client";

import React, { useState } from "react";
import { TradeProposal, OrderRecord } from "@/lib/types";
import { api } from "@/lib/api";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Clock,
  ArrowRight,
  CheckCircle,
  XCircle,
  Lock,
  PieChart,
  DollarSign,
  Layers,
} from "lucide-react";
import Link from "next/link";

interface TradeReviewCardProps {
  proposal: TradeProposal;
  onTradeConfirmed?: (order: OrderRecord) => void;
  onCancelled?: () => void;
}

export function TradeReviewCard({
  proposal,
  onTradeConfirmed,
  onCancelled,
}: TradeReviewCardProps) {
  const [confirming, setConfirming] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [executedOrder, setExecutedOrder] = useState<OrderRecord | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isBuy = proposal.side === "BUY";
  const canExecute = proposal.risk.can_execute;
  const overallStatus = proposal.risk.overall_status;

  const handleConfirm = async () => {
    if (!canExecute) return;
    try {
      setConfirming(true);
      setErrorMessage(null);
      const order = await api.confirmTrade(proposal.id);
      setExecutedOrder(order);
      if (onTradeConfirmed) onTradeConfirmed(order);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to execute order.");
    } finally {
      setConfirming(false);
    }
  };

  const handleCancel = async () => {
    try {
      setCancelling(true);
      await api.cancelTrade(proposal.id);
      if (onCancelled) onCancelled();
    } catch (err: any) {
      console.error(err);
    } finally {
      setCancelling(false);
    }
  };

  // If already executed, render the trade fulfillment receipt
  if (executedOrder) {
    return (
      <div className="w-full rounded-2xl border border-accent/40 bg-surface p-6 shadow-card transition-all">
        <div className="flex items-center gap-3 pb-4 border-b border-border">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-surface text-accent border border-accent/30">
            <CheckCircle className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-fg">
                Order Executed & Settled
              </h3>
              <span className="rounded px-1.5 py-0.5 font-mono text-[10px] font-bold bg-accent-surface text-accent">
                {executedOrder.status}
              </span>
            </div>
            <p className="text-xs text-fg-subtle">
              Fulfilled via {executedOrder.mode} environment with deterministic settlement
            </p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 rounded-xl border border-border bg-canvas-subtle p-3.5 font-mono text-xs">
          <div>
            <span className="text-fg-subtle block text-[10px] uppercase font-sans">
              Asset & Side
            </span>
            <span className="font-semibold text-fg">
              {executedOrder.side} {executedOrder.asset}
            </span>
          </div>
          <div>
            <span className="text-fg-subtle block text-[10px] uppercase font-sans">
              Quantity
            </span>
            <span className="font-semibold text-fg tabular-nums">
              {executedOrder.quantity.toLocaleString(undefined, {
                maximumFractionDigits: 6,
              })}
            </span>
          </div>
          <div>
            <span className="text-fg-subtle block text-[10px] uppercase font-sans">
              Notional Value
            </span>
            <span className="font-semibold text-fg tabular-nums">
              ${executedOrder.notional_usd.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
            </span>
          </div>
          <div>
            <span className="text-fg-subtle block text-[10px] uppercase font-sans">
              Order Reference
            </span>
            <span className="font-semibold text-fg truncate block">
              {executedOrder.external_order_id || executedOrder.id}
            </span>
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between pt-3 border-t border-border">
          <Link
            href="/app/activity"
            className="flex items-center gap-1.5 text-xs font-semibold text-accent hover:text-accent-dark transition-colors"
          >
            <span>View In Immutable Audit Trail</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
          <button
            type="button"
            suppressHydrationWarning
            onClick={() => {
              setExecutedOrder(null);
              if (onCancelled) onCancelled();
            }}
            className="text-xs font-medium text-fg-subtle hover:text-fg transition-colors"
          >
            Compose New Intent
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full rounded-2xl border border-border bg-surface shadow-card overflow-hidden transition-all">
      {/* Top Banner: Security and Human Gate Invariant */}
      <div className="flex items-center justify-between border-b border-border bg-canvas-subtle px-5 py-2.5 text-xs">
        <div className="flex items-center gap-2 text-fg-muted font-medium">
          <Lock className="h-3.5 w-3.5 text-accent" />
          <span className="font-mono text-[11px] uppercase tracking-wider font-semibold">
            Pre-Trade Review · Human Gate Enforced
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] font-mono text-fg-subtle">
          <Clock className="h-3 w-3 text-accent" />
          <span>Quote TTL: 30s</span>
        </div>
      </div>

      <div className="p-5 sm:p-6 space-y-5">
        {/* Core Order Details: Side, Asset, Notional, Fill */}
        <div className="flex flex-wrap items-baseline justify-between gap-4 pb-4 border-b border-border">
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded font-mono text-xs font-bold border ${
                  isBuy
                    ? "bg-accent-surface text-accent border-accent/30"
                    : "bg-warn-surface text-warn border-warn/30"
                }`}
              >
                {proposal.side}
              </span>
              <span className="text-xl font-bold tracking-tight text-fg">
                {proposal.asset}
              </span>
              <span className="text-xs text-fg-subtle font-mono">
                {proposal.quote.pair}
              </span>
            </div>
            <div className="mt-1.5 flex items-baseline gap-1">
              <span className="text-3xl font-bold tracking-tight text-fg tabular-nums font-sans">
                ${proposal.estimated_notional_usd.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                })}
              </span>
              <span className="text-xs font-medium text-fg-subtle">USD</span>
            </div>
          </div>

          <div className="text-left sm:text-right">
            <span className="text-[11px] text-fg-subtle uppercase tracking-wider font-semibold block">
              Estimated Fill
            </span>
            <span className="font-mono text-lg font-semibold text-fg tabular-nums">
              {proposal.estimated_qty.toLocaleString(undefined, {
                maximumFractionDigits: 6,
              })}{" "}
              <span className="text-sm font-normal text-fg-subtle font-sans">
                {proposal.asset}
              </span>
            </span>
          </div>
        </div>

        {/* Live Market Quote Snapshot */}
        <div className="rounded-xl border border-border bg-canvas-subtle p-3.5 text-xs">
          <div className="flex items-center justify-between text-fg-subtle pb-2 border-b border-border font-mono text-[10px]">
            <span className="uppercase tracking-wider font-bold text-fg-muted font-sans">
              Market Context
            </span>
            <span className="text-accent flex items-center gap-1 font-sans">
              <span className="h-1.5 w-1.5 rounded-full bg-accent" />
              {proposal.quote.source}
            </span>
          </div>
          <div className="mt-2.5 grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
            <div>
              <span className="text-fg-subtle block text-[10px]">Mid Price</span>
              <span className="text-fg font-medium tabular-nums">
                ${proposal.quote.mid.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                })}
              </span>
            </div>
            <div>
              <span className="text-fg-subtle block text-[10px]">
                {isBuy ? "Ask (Execution)" : "Bid (Execution)"}
              </span>
              <span className="text-fg font-medium tabular-nums">
                ${(isBuy ? proposal.quote.ask : proposal.quote.bid).toLocaleString(
                  undefined,
                  { minimumFractionDigits: 2 }
                )}
              </span>
            </div>
            <div>
              <span className="text-fg-subtle block text-[10px]">Spread</span>
              <span className="text-fg font-medium tabular-nums">
                {proposal.quote.spread_pct}%
              </span>
            </div>
            <div>
              <span className="text-fg-subtle block text-[10px]">Freshness</span>
              <span className="text-fg font-medium">30s TTL Window</span>
            </div>
          </div>
        </div>

        {/* Portfolio Impact Modeling */}
        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-fg-muted flex items-center gap-1.5">
              <PieChart className="h-3.5 w-3.5 text-accent" />
              <span>Projected Portfolio Impact</span>
            </h4>
            <span className="text-[11px] font-mono text-fg-subtle">
              Total: ${proposal.portfolio_impact.total_portfolio_value_before.toLocaleString(
                undefined,
                { minimumFractionDigits: 2 }
              )}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {/* Asset Allocation Shift */}
            <div className="rounded-lg bg-canvas-subtle p-3 text-xs">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-fg-subtle">
                  {proposal.asset} Portfolio Share
                </span>
                <div className="flex items-center gap-1.5 font-mono">
                  <span className="text-fg font-semibold tabular-nums">
                    {proposal.portfolio_impact.current_allocation_pct}%
                  </span>
                  <ArrowRight className="h-3 w-3 text-fg-subtle" />
                  <span
                    className={`font-bold tabular-nums ${
                      proposal.portfolio_impact.projected_allocation_pct > 35
                        ? "text-warn"
                        : "text-accent"
                    }`}
                  >
                    {proposal.portfolio_impact.projected_allocation_pct}%
                  </span>
                </div>
              </div>
              <div className="mt-2 h-1.5 w-full bg-border rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    proposal.portfolio_impact.projected_allocation_pct > 35
                      ? "bg-warn"
                      : "bg-accent"
                  }`}
                  style={{
                    width: `${Math.min(
                      100,
                      Math.max(2, proposal.portfolio_impact.projected_allocation_pct)
                    )}%`,
                  }}
                />
              </div>
            </div>

            {/* Cash Impact */}
            <div className="rounded-lg bg-canvas-subtle p-3 text-xs">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-fg-subtle">Cash Balance (USDC)</span>
                <div className="flex items-center gap-1.5 font-mono">
                  <span className="text-fg font-semibold tabular-nums">
                    ${proposal.portfolio_impact.cash_before_usd.toLocaleString(
                      undefined,
                      { minimumFractionDigits: 2 }
                    )}
                  </span>
                  <ArrowRight className="h-3 w-3 text-fg-subtle" />
                  <span className="text-fg font-bold tabular-nums">
                    ${proposal.portfolio_impact.cash_after_usd.toLocaleString(
                      undefined,
                      { minimumFractionDigits: 2 }
                    )}
                  </span>
                </div>
              </div>
              <span className="mt-2 block text-[10px] text-fg-subtle">
                Settled balance updated upon confirmation
              </span>
            </div>
          </div>
        </div>

        {/* Deterministic Risk Checks Matrix */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-fg-muted flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-accent" />
              <span>Deterministic Risk Engine Verification</span>
            </h4>
            <span
              className={`rounded px-2 py-0.5 font-mono text-[10px] font-bold border ${
                overallStatus === "PASS"
                  ? "bg-accent-surface text-accent border-accent/30"
                  : overallStatus === "WARN"
                  ? "bg-warn-surface text-warn border-warn/30"
                  : "bg-danger-surface text-danger border-danger/30"
              }`}
            >
              {overallStatus}
            </span>
          </div>

          <div className="space-y-1.5">
            {proposal.risk.checks.map((check, idx) => {
              const isPass = check.status === "PASS";
              const isWarn = check.status === "WARN";
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-2.5 rounded-lg border p-2.5 text-xs transition-colors ${
                    isPass
                      ? "border-border bg-canvas-subtle"
                      : isWarn
                      ? "border-warn/30 bg-warn-surface"
                      : "border-danger/30 bg-danger-surface"
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    {isPass && (
                      <CheckCircle className="h-3.5 w-3.5 text-accent" />
                    )}
                    {isWarn && (
                      <AlertTriangle className="h-3.5 w-3.5 text-warn" />
                    )}
                    {!isPass && !isWarn && (
                      <XCircle className="h-3.5 w-3.5 text-danger" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-fg text-xs truncate">
                        {check.name}
                      </span>
                      <span
                        className={`font-mono text-[10px] font-bold shrink-0 ${
                          isPass
                            ? "text-accent"
                            : isWarn
                            ? "text-warn"
                            : "text-danger"
                        }`}
                      >
                        {check.status}
                      </span>
                    </div>
                    <p className="text-fg-muted text-[11px] mt-0.5 leading-relaxed">
                      {check.message}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Explainable Proposal Summary */}
        <div className="rounded-xl border border-border bg-canvas-subtle p-3 text-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-fg-subtle block mb-1">
            System Rationale
          </span>
          <p className="text-fg-muted leading-relaxed text-[11px]">
            {proposal.explanation}
          </p>
        </div>

        {/* Error notification if confirmation failed */}
        {errorMessage && (
          <div className="rounded-lg border border-danger/30 bg-danger-surface p-3 text-xs text-danger flex items-center gap-2">
            <XCircle className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Deliberate Confirmation Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="button"
            suppressHydrationWarning
            onClick={handleCancel}
            disabled={cancelling || confirming}
            className="flex-1 rounded-xl border border-border bg-surface px-4 py-3 text-xs font-semibold text-fg hover:bg-surface-hover transition-colors shadow-subtle"
          >
            {cancelling ? "Cancelling..." : "Cancel"}
          </button>

          <button
            type="button"
            suppressHydrationWarning
            onClick={handleConfirm}
            disabled={!canExecute || confirming || cancelling}
            className={`flex-1 rounded-xl px-4 py-3 text-xs font-semibold text-white shadow-subtle transition-all flex items-center justify-center gap-2 ${
              canExecute
                ? "bg-accent hover:bg-accent-dark"
                : "bg-fg-subtle opacity-40 cursor-not-allowed"
            }`}
          >
            {confirming ? (
              <span className="flex items-center gap-2">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Executing Order...
              </span>
            ) : canExecute ? (
              <span className="flex items-center gap-1.5">
                <Lock className="h-3.5 w-3.5" />
                <span>Confirm & Execute Trade</span>
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <ShieldAlert className="h-3.5 w-3.5" />
                <span>Blocked by Risk Engine</span>
              </span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
