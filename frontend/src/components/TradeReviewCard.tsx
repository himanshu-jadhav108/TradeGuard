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
  TrendingUp,
  Wallet,
  Lock,
  ExternalLink,
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

  // If already executed, display success receipt
  if (executedOrder) {
    return (
      <div className="w-full rounded-2xl border border-emerald/30 bg-surface p-6 shadow-card transition-all">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-surface text-emerald">
            <CheckCircle className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-fg">
              Trade Successfully Executed
            </h3>
            <p className="text-xs text-fg-subtle">
              Deterministic order fulfilled via {executedOrder.mode} environment
            </p>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3 rounded-xl border border-border bg-canvas-subtle p-4 font-mono text-xs">
          <div>
            <span className="text-fg-subtle block">Status</span>
            <span className="font-semibold text-emerald">
              {executedOrder.status}
            </span>
          </div>
          <div>
            <span className="text-fg-subtle block">Quantity</span>
            <span className="font-semibold text-fg">
              {executedOrder.quantity.toLocaleString(undefined, {
                maximumFractionDigits: 6,
              })}{" "}
              {executedOrder.asset}
            </span>
          </div>
          <div>
            <span className="text-fg-subtle block">Notional</span>
            <span className="font-semibold text-fg">
              ${executedOrder.notional_usd.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
            </span>
          </div>
          <div>
            <span className="text-fg-subtle block">External Ref</span>
            <span className="font-semibold text-fg truncate block">
              {executedOrder.external_order_id}
            </span>
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between pt-3 border-t border-border">
          <Link
            href="/app/activity"
            className="flex items-center gap-1.5 text-xs font-medium text-emerald hover:text-emerald-dark transition-colors"
          >
            <span>View in Audit Activity</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
          <button
            onClick={() => {
              setExecutedOrder(null);
              if (onCancelled) onCancelled();
            }}
            className="text-xs text-fg-subtle hover:text-fg transition-colors"
          >
            Review New Trade
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full rounded-2xl border border-border bg-surface shadow-card overflow-hidden transition-all">
      {/* Top Banner: AI Analysis ≠ Execution */}
      <div className="flex items-center justify-between border-b border-border bg-canvas-subtle px-5 py-3 text-xs">
        <div className="flex items-center gap-2 text-fg-muted font-medium">
          <Lock className="h-3.5 w-3.5 text-emerald" />
          <span>Execution Boundary: Explicit Human Confirmation Required</span>
        </div>
        <div className="flex items-center gap-1 text-[11px] text-fg-subtle">
          <Clock className="h-3 w-3" />
          <span>TTL: 30s</span>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Header: Trade Side & Amount */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide ${
                  isBuy
                    ? "bg-emerald-surface text-emerald border border-emerald/20"
                    : "bg-warn-surface text-warn border border-warn/20"
                }`}
              >
                {proposal.side} {proposal.asset}
              </span>
              <span className="text-sm text-fg-subtle font-mono">
                {proposal.quote.pair}
              </span>
            </div>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-fg">
              ${proposal.estimated_notional_usd.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}{" "}
              <span className="text-sm font-normal text-fg-subtle">USD</span>
            </h2>
          </div>

          <div className="text-right">
            <span className="text-xs text-fg-subtle block">Estimated Fill</span>
            <span className="font-mono text-xl font-semibold text-fg">
              {proposal.estimated_qty.toLocaleString(undefined, {
                maximumFractionDigits: 6,
              })}{" "}
              {proposal.asset}
            </span>
          </div>
        </div>

        {/* Live Quote Details Box */}
        <div className="rounded-xl border border-border bg-canvas-subtle p-4 text-xs font-mono">
          <div className="flex items-center justify-between text-fg-subtle pb-2 border-b border-border">
            <span className="uppercase text-[10px] tracking-wider font-sans font-semibold">
              Live Quote Snapshot
            </span>
            <span className="text-[11px] text-emerald">
              ● {proposal.quote.source}
            </span>
          </div>
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <span className="text-fg-subtle block text-[11px]">Mid Price</span>
              <span className="text-fg font-medium">
                ${proposal.quote.mid.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                })}
              </span>
            </div>
            <div>
              <span className="text-fg-subtle block text-[11px]">
                {isBuy ? "Ask (Fill Price)" : "Bid"}
              </span>
              <span className="text-fg font-medium">
                ${(isBuy ? proposal.quote.ask : proposal.quote.bid).toLocaleString(
                  undefined,
                  { minimumFractionDigits: 2 }
                )}
              </span>
            </div>
            <div>
              <span className="text-fg-subtle block text-[11px]">Spread</span>
              <span className="text-fg font-medium">
                {proposal.quote.spread_pct}%
              </span>
            </div>
            <div>
              <span className="text-fg-subtle block text-[11px]">Quote Time</span>
              <span className="text-fg font-medium truncate block">
                {new Date(proposal.quote.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>

        {/* Portfolio Impact Section */}
        <div className="rounded-xl border border-border p-4 bg-surface">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-fg-muted" />
            <h4 className="text-xs font-semibold uppercase tracking-wider text-fg-muted">
              Projected Portfolio Impact
            </h4>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Allocation Shift */}
            <div className="rounded-lg bg-canvas-subtle p-3 text-xs">
              <span className="text-fg-subtle block text-[11px]">
                {proposal.asset} Allocation Shift
              </span>
              <div className="mt-1 flex items-center gap-2 font-mono">
                <span className="text-fg font-semibold">
                  {proposal.portfolio_impact.current_allocation_pct}%
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-fg-subtle" />
                <span
                  className={`font-semibold ${
                    proposal.portfolio_impact.projected_allocation_pct > 35
                      ? "text-warn"
                      : "text-emerald"
                  }`}
                >
                  {proposal.portfolio_impact.projected_allocation_pct}%
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full bg-border rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    proposal.portfolio_impact.projected_allocation_pct > 35
                      ? "bg-warn"
                      : "bg-emerald"
                  }`}
                  style={{
                    width: `${Math.min(
                      100,
                      proposal.portfolio_impact.projected_allocation_pct
                    )}%`,
                  }}
                />
              </div>
            </div>

            {/* Cash Impact */}
            <div className="rounded-lg bg-canvas-subtle p-3 text-xs">
              <span className="text-fg-subtle block text-[11px]">
                Cash Balance Impact
              </span>
              <div className="mt-1 flex items-center gap-2 font-mono">
                <span className="text-fg font-semibold">
                  ${proposal.portfolio_impact.cash_before_usd.toLocaleString(
                    undefined,
                    { minimumFractionDigits: 2 }
                  )}
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-fg-subtle" />
                <span className="font-semibold text-fg">
                  ${proposal.portfolio_impact.cash_after_usd.toLocaleString(
                    undefined,
                    { minimumFractionDigits: 2 }
                  )}
                </span>
              </div>
              <span className="text-[10px] text-fg-subtle mt-1.5 block">
                Total portfolio value: $
                {proposal.portfolio_impact.total_portfolio_value_before.toLocaleString(
                  undefined,
                  { minimumFractionDigits: 2 }
                )}
              </span>
            </div>
          </div>
        </div>

        {/* Deterministic Risk Checks */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-fg-muted flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald" />
              <span>Deterministic Risk Engine Verification</span>
            </h4>
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                proposal.risk.overall_status === "PASS"
                  ? "bg-emerald-surface text-emerald"
                  : proposal.risk.overall_status === "WARN"
                  ? "bg-warn-surface text-warn"
                  : "bg-danger-surface text-danger"
              }`}
            >
              {proposal.risk.overall_status}
            </span>
          </div>

          <div className="space-y-2">
            {proposal.risk.checks.map((check, idx) => {
              const isPass = check.status === "PASS";
              const isWarn = check.status === "WARN";
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-2.5 rounded-lg border p-2.5 text-xs transition-colors ${
                    isPass
                      ? "border-border bg-surface"
                      : isWarn
                      ? "border-warn/30 bg-warn-surface"
                      : "border-danger/30 bg-danger-surface"
                  }`}
                >
                  <div className="mt-0.5">
                    {isPass && (
                      <CheckCircle className="h-4 w-4 text-emerald" />
                    )}
                    {isWarn && (
                      <AlertTriangle className="h-4 w-4 text-warn" />
                    )}
                    {!isPass && !isWarn && (
                      <XCircle className="h-4 w-4 text-danger" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-fg">
                        {check.name}
                      </span>
                      <span
                        className={`text-[10px] font-mono font-bold ${
                          isPass
                            ? "text-emerald"
                            : isWarn
                            ? "text-warn"
                            : "text-danger"
                        }`}
                      >
                        {check.status}
                      </span>
                    </div>
                    <p className="text-fg-muted text-[11px] mt-0.5">
                      {check.message}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Explainable AI Justification */}
        <div className="rounded-xl border border-border bg-canvas-subtle p-3.5 text-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-fg-subtle block mb-1">
            Explainable Proposal Summary
          </span>
          <p className="text-fg-muted leading-relaxed">
            {proposal.explanation}
          </p>
        </div>

        {/* Error Notification if confirm fails */}
        {errorMessage && (
          <div className="rounded-lg border border-danger/40 bg-danger-surface p-3 text-xs text-danger flex items-center gap-2">
            <XCircle className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Action Buttons: Cancel vs Explicit Confirm */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="button"
            onClick={handleCancel}
            disabled={cancelling || confirming}
            className="flex-1 rounded-xl border border-border bg-surface px-4 py-3 text-xs font-semibold text-fg hover:bg-surface-hover transition-colors"
          >
            {cancelling ? "Cancelling..." : "Cancel"}
          </button>

          <button
            type="button"
            onClick={handleConfirm}
            disabled={!canExecute || confirming || cancelling}
            className={`flex-1 rounded-xl px-4 py-3 text-xs font-semibold text-white shadow-md transition-all flex items-center justify-center gap-2 ${
              canExecute
                ? "bg-emerald hover:bg-emerald-dark"
                : "bg-fg-subtle opacity-50 cursor-not-allowed"
            }`}
          >
            {confirming ? (
              <span className="flex items-center gap-2">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Executing Order...
              </span>
            ) : canExecute ? (
              <span>Confirm Trade</span>
            ) : (
              <span>Blocked by Risk Engine</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
