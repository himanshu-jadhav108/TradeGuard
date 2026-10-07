"use client";

import React, { useState, useEffect } from "react";
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
  RefreshCw,
  Info,
} from "lucide-react";

interface TradeReviewCardProps {
  proposal: TradeProposal;
  onTradeConfirmed?: (order: OrderRecord) => void;
  onCancelled?: () => void;
  onRefreshQuote?: (newProposal: TradeProposal) => void;
}

export function TradeReviewCard({
  proposal,
  onTradeConfirmed,
  onCancelled,
  onRefreshQuote,
}: TradeReviewCardProps) {
  const [confirming, setConfirming] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [acknowledgedWarning, setAcknowledgedWarning] = useState(false);
  const [executedOrder, setExecutedOrder] = useState<OrderRecord | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(30);

  const isBuy = proposal.side === "BUY";
  const canExecute = proposal.risk.can_execute;
  const overallStatus = proposal.risk.overall_status;
  const isWarn = overallStatus === "WARN";
  const isBlock = overallStatus === "BLOCK";
  const isDemo = proposal.quote.source !== "TRUE_MARKETS_UAT";

  // Derive dynamic concentration threshold from deterministic check details (avoid hardcoding 40)
  const concentrationCheck = proposal.risk.checks.find((c) =>
    c.name.toLowerCase().includes("concentration")
  );
  const concentrationThreshold = Number(
    concentrationCheck?.details?.threshold_pct ??
    (concentrationCheck?.details?.threshold
      ? String(concentrationCheck.details.threshold).replace("%", "")
      : 40)
  );

  // Live countdown timer based on backend expires_at timestamp
  useEffect(() => {
    const updateCountdown = () => {
      const expiresAt = new Date(proposal.expires_at).getTime();
      const now = Date.now();
      const remaining = Math.max(0, Math.floor((expiresAt - now) / 1000));
      setSecondsRemaining(remaining);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [proposal.expires_at]);

  const isExpired = secondsRemaining <= 0;

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setErrorMessage(null);
      const fallbackPrompt =
        proposal.request_amount_type === "ASSET"
          ? `${proposal.side} ${proposal.request_amount} ${proposal.asset}`
          : `${proposal.side} $${proposal.request_amount} of ${proposal.asset}`;
      const promptToUse = proposal.raw_prompt || fallbackPrompt;
      const newProposal = await api.createProposal(promptToUse);
      if (onRefreshQuote) {
        onRefreshQuote(newProposal);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to refresh market quote.");
    } finally {
      setRefreshing(false);
    }
  };

  const handleConfirm = async () => {
    if (!canExecute || isExpired) return;
    if (isWarn && !acknowledgedWarning) return;

    try {
      setConfirming(true);
      setErrorMessage(null);
      const order = await api.confirmTrade(proposal.id, acknowledgedWarning);
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
      setErrorMessage(null);
      await api.cancelTrade(proposal.id);
      if (onCancelled) onCancelled();
    } catch (err: any) {
      console.error("Cancel trade error:", err);
      setErrorMessage(err.message || "Failed to cancel proposal.");
    } finally {
      setCancelling(false);
    }
  };

  // If order was executed, render truthful settlement receipt
  if (executedOrder) {
    const isFilled = executedOrder.status === "FILLED";
    const isSubmitted = executedOrder.status === "SUBMITTED";
    const isFailed = executedOrder.status === "FAILED" || executedOrder.status === "REJECTED";

    let receiptTitle = isDemo ? "Simulated Order Filled" : "Order Executed on True Markets";
    let receiptSubtitle = isDemo
      ? "Simulated deterministic fill · Account balances updated"
      : `Gateway order executed · External ID: ${executedOrder.external_order_id}`;
    let lifecycleStatus = isDemo ? "Simulated Fill" : "Settled";
    let activeSegments = 4;

    if (isSubmitted) {
      receiptTitle = isDemo ? "Simulated Order Submitted" : "Order Submitted to True Markets Gateway";
      receiptSubtitle = isDemo
        ? "Submitted to simulation queue · Awaiting settlement"
        : `Dispatched to Gateway · Awaiting fill · External ID: ${executedOrder.external_order_id}`;
      lifecycleStatus = "Submitted (Pending Fill)";
      activeSegments = 3;
    } else if (isFailed) {
      receiptTitle = "Order Execution Failed";
      receiptSubtitle = `Execution was not completed by gateway · External ID: ${executedOrder.external_order_id || "None"}`;
      lifecycleStatus = "Execution Failed";
      activeSegments = 2;
    } else if (!isFilled) {
      receiptTitle = `Order ${executedOrder.status}`;
      receiptSubtitle = `Current status: ${executedOrder.status} · External ID: ${executedOrder.external_order_id || "None"}`;
      lifecycleStatus = executedOrder.status;
      activeSegments = 2;
    }

    // Price label: "Reference Price" unless FILLED with a gateway fill price (or simulated fill in demo)
    let priceLabel = "Reference Price";
    let displayPrice = executedOrder.fill_price
      ? `$${executedOrder.fill_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
      : `$${proposal.quote.mid.toLocaleString(undefined, { minimumFractionDigits: 2 })} (Ref)`;

    if (isFilled && !isDemo && executedOrder.fill_price) {
      priceLabel = "Gateway Fill Price";
      displayPrice = `$${executedOrder.fill_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
    } else if (isFilled && isDemo && executedOrder.fill_price) {
      priceLabel = "Simulated Fill Price";
      displayPrice = `$${executedOrder.fill_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
    }

    return (
      <div className={`w-full rounded-2xl border ${isFailed ? "border-danger/40" : isSubmitted ? "border-warn/40" : "border-accent/40"} bg-surface p-6 shadow-card transition-all`}>
        <div className="flex items-center gap-3 pb-4 border-b border-border">
          <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${
            isFailed
              ? "bg-danger-surface text-danger border border-danger/30"
              : isSubmitted
              ? "bg-warn-surface text-warn border border-warn/30"
              : "bg-accent-surface text-accent border border-accent/30"
          }`}>
            {isFailed ? (
              <XCircle className="h-5 w-5" />
            ) : isSubmitted ? (
              <Clock className="h-5 w-5" />
            ) : (
              <CheckCircle className="h-5 w-5" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-fg">
                {receiptTitle}
              </h3>
              <span className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-bold ${
                isFailed
                  ? "bg-danger-surface text-danger"
                  : isSubmitted
                  ? "bg-warn-surface text-warn-text border border-warn/30"
                  : "bg-accent-surface text-accent"
              }`}>
                {executedOrder.status}
              </span>
            </div>
            <p className="text-xs text-fg-subtle">
              {receiptSubtitle}
            </p>
          </div>
        </div>

        {/* Order Lifecycle Progress */}
        <div className="my-5 p-4 rounded-xl bg-canvas-subtle border border-border">
          <div className="flex items-center justify-between text-xs font-mono text-fg-muted mb-2">
            <span className="text-[11px] uppercase font-sans font-semibold text-fg">
              Execution Lifecycle
            </span>
            <span className={`text-[11px] ${isFailed ? "text-danger" : isSubmitted ? "text-warn" : "text-accent"} font-semibold`}>
              {lifecycleStatus}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className={`flex-1 h-1.5 rounded-full ${activeSegments >= 1 ? "bg-accent" : "bg-border"}`} />
            <div className={`flex-1 h-1.5 rounded-full ${activeSegments >= 2 ? "bg-accent" : "bg-border"}`} />
            <div className={`flex-1 h-1.5 rounded-full ${isFailed ? "bg-danger" : activeSegments >= 3 ? "bg-accent" : "bg-border"}`} />
            <div className={`flex-1 h-1.5 rounded-full ${isFailed ? "bg-border" : activeSegments >= 4 ? "bg-accent" : "bg-border"}`} />
          </div>
          <div className="flex items-center justify-between text-[10px] font-mono text-fg-subtle mt-2">
            <span className={activeSegments >= 1 ? "text-fg font-medium" : ""}>Review</span>
            <span className={activeSegments >= 2 ? "text-fg font-medium" : ""}>Confirmed</span>
            <span className={isSubmitted ? "text-warn font-semibold" : activeSegments >= 3 ? "text-fg font-medium" : ""}>Submitted</span>
            <span className={isFilled ? "text-accent font-semibold" : ""}>Filled</span>
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
              {priceLabel}
            </span>
            <span className="font-semibold text-fg tabular-nums">
              {displayPrice}
            </span>
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => {
              setExecutedOrder(null);
              if (onCancelled) onCancelled();
            }}
            className="rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white hover:bg-accent-dark transition-all"
          >
            Create New Trade Intent
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full rounded-2xl border border-border bg-surface shadow-card overflow-hidden transition-all">
      {/* 1. Header Banner & Safety Verdict */}
      <div
        className={`p-5 sm:p-6 border-b ${
          isBlock
            ? "border-danger/30 bg-danger-surface"
            : isWarn
            ? "border-warn/30 bg-warn-surface"
            : "border-accent/20 bg-accent-surface/30"
        }`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${
                isBlock
                  ? "bg-danger text-white border-danger"
                  : isWarn
                  ? "bg-warn text-white border-warn"
                  : "bg-accent text-white border-accent"
              }`}
            >
              {isBlock ? (
                <ShieldAlert className="h-5 w-5" />
              ) : isWarn ? (
                <AlertTriangle className="h-5 w-5" />
              ) : (
                <ShieldCheck className="h-5 w-5" />
              )}
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-fg-muted font-mono">
                  Pre-Trade Safety Evaluation
                </span>
                <span
                  className={`rounded px-2 py-0.5 font-mono text-[10px] font-bold border ${
                    isBlock
                      ? "bg-danger text-white border-danger"
                      : isWarn
                      ? "bg-warn-surface text-warn-text border-warn/30"
                      : "bg-accent-surface text-accent border-accent/20"
                  }`}
                >
                  {overallStatus}
                </span>
                <span className="rounded px-2 py-0.5 font-mono text-[10px] font-medium bg-canvas-subtle border border-border text-fg-subtle">
                  {isDemo ? "Demo · Simulated" : "True Markets UAT"}
                </span>
              </div>

              <h2 className="text-lg sm:text-xl font-bold text-fg mt-1 tracking-tight">
                {isBlock
                  ? "Trade Blocked by Safety Guardrail"
                  : isWarn
                  ? "Review Warning: Exceeds Concentration Limit"
                  : "Safety Verified: Safe for Confirmation"}
              </h2>

              <p className="text-xs text-fg-muted mt-1 leading-relaxed max-w-2xl">
                {proposal.explanation}
              </p>
            </div>
          </div>

          {/* Freshness Countdown & Refresh Button */}
          <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2 shrink-0">
            <div
              aria-live="polite"
              aria-atomic="true"
              className={`flex items-center gap-1.5 font-mono text-xs px-2.5 py-1 rounded-lg border ${
                isExpired
                  ? "bg-danger-surface text-danger border-danger/30 animate-pulse"
                  : secondsRemaining <= 10
                  ? "bg-warn-surface text-warn border-warn/30"
                  : "bg-canvas-subtle text-fg-muted border-border"
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              <span>{isExpired ? "Quote Expired" : `${secondsRemaining}s TTL`}</span>
            </div>

            {isExpired && (
              <button
                type="button"
                onClick={handleRefresh}
                disabled={refreshing}
                className="text-xs text-accent hover:text-accent-dark font-medium flex items-center gap-1 transition-colors"
              >
                <RefreshCw className={`h-3 w-3 ${refreshing ? "animate-spin" : ""}`} />
                <span>Refresh Quote</span>
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="p-5 sm:p-6 space-y-6">
        {/* 2. Intent Disambiguation: "You said" vs "We understood" */}
        <div className="rounded-xl border border-border bg-canvas-subtle p-4 font-mono text-xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-border text-[11px] font-sans">
            <span className="font-semibold text-fg-muted uppercase tracking-wider">
              Intent Translation Grounding
            </span>
            <span className="text-fg-subtle text-[10px]">Deterministic Parser</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span className="text-[10px] text-fg-subtle uppercase block mb-1 font-sans">
                You Said:
              </span>
              <p className="text-fg font-sans italic bg-surface p-2.5 rounded-lg border border-border">
                “{proposal.raw_prompt || `${proposal.side} $${proposal.request_amount} of ${proposal.asset}`}”
              </p>
            </div>
            <div>
              <span className="text-[10px] text-fg-subtle uppercase block mb-1 font-sans">
                We Understood:
              </span>
              <div className="flex items-center gap-2 bg-surface p-2.5 rounded-lg border border-border font-bold">
                <span className={isBuy ? "text-accent" : "text-danger"}>
                  {proposal.side}
                </span>
                <span className="text-fg">{proposal.asset}</span>
                <span className="text-fg-muted">·</span>
                <span className="text-fg tabular-nums">
                  ${proposal.estimated_notional_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })} USD
                </span>
                <span className="text-fg-subtle font-normal text-[11px]">
                  ({proposal.estimated_qty.toLocaleString(undefined, { maximumFractionDigits: 6 })} {proposal.asset})
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 3. Market Quote & Parameters */}
        <div className="rounded-xl border border-border bg-surface p-4 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-fg-muted">
              Market Quote & Execution Parameters
            </h4>
            <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono text-fg-subtle">
              <span>Source: <strong className="text-fg-muted">{proposal.quote.source}</strong></span>
              <span>·</span>
              <span>{new Date(proposal.quote.timestamp).toISOString().replace("T", " ").substring(0, 19)} UTC</span>
              <span>·</span>
              <span>Age: <strong className="text-fg-muted">{(proposal.quote.age_seconds ?? Math.max(0, (Date.now() - new Date(proposal.quote.timestamp).getTime()) / 1000)).toFixed(1)}s</strong></span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
            <div>
              <span className="text-fg-subtle block text-[10px]">Quoted Price</span>
              <span className="text-fg font-bold tabular-nums">
                ${(isBuy ? proposal.quote.ask : proposal.quote.bid).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div>
              <span className="text-fg-subtle block text-[10px]">Estimated Quantity</span>
              <span className="text-fg font-bold tabular-nums">
                {proposal.estimated_qty.toLocaleString(undefined, { maximumFractionDigits: 6 })} {proposal.asset}
              </span>
            </div>
            <div>
              <span className="text-fg-subtle block text-[10px]">Spread</span>
              <span className="text-fg font-medium tabular-nums">
                {proposal.quote.spread_pct}%
              </span>
            </div>
            <div>
              <span className="text-fg-subtle block text-[10px]">Fees</span>
              <span className="text-fg-muted font-sans text-xs">
                {proposal.fee_label || "Not modelled in demo"}
              </span>
            </div>
          </div>
        </div>

        {/* 4. Portfolio Impact Modeling */}
        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-fg-muted flex items-center gap-1.5">
              <PieChart className="h-3.5 w-3.5 text-accent" />
              <span>Projected Portfolio Impact</span>
            </h4>
            <span className="text-[11px] font-mono text-fg-subtle">
              Total Portfolio: ${proposal.portfolio_impact.total_portfolio_value_before.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {/* Allocation Shift */}
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
                      proposal.portfolio_impact.projected_allocation_pct > concentrationThreshold
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
                    proposal.portfolio_impact.projected_allocation_pct > concentrationThreshold
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
              <span className="mt-1.5 block text-[10px] text-fg-subtle">
                Guideline threshold: {concentrationThreshold}% maximum allocation
              </span>
            </div>

            {/* Cash Impact */}
            <div className="rounded-lg bg-canvas-subtle p-3 text-xs">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-fg-subtle">Cash Balance (USDC)</span>
                <div className="flex items-center gap-1.5 font-mono">
                  <span className="text-fg font-semibold tabular-nums">
                    ${proposal.portfolio_impact.cash_before_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                  <ArrowRight className="h-3 w-3 text-fg-subtle" />
                  <span className="text-fg font-bold tabular-nums">
                    ${proposal.portfolio_impact.cash_after_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
              <span className="mt-2 block text-[10px] text-fg-subtle">
                Settled liquid purchasing power
              </span>
            </div>
          </div>
        </div>

        {/* 5. Deterministic Risk Checks List */}
        <div className="space-y-2">
          <h4 className="text-[11px] font-semibold uppercase tracking-wider text-fg-muted flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-accent" />
            <span>Deterministic Risk Rules</span>
          </h4>
          <div className="space-y-2">
            {proposal.risk.checks.map((check, idx) => {
              const checkPass = check.status === "PASS";
              const checkWarn = check.status === "WARN";
              return (
                <div
                  key={idx}
                  style={{ animationDelay: `${idx * 45}ms` }}
                  className={`flex items-start justify-between gap-3 p-3 rounded-xl border text-xs animate-fadeIn ${
                    checkPass
                      ? "bg-canvas-subtle border-border"
                      : checkWarn
                      ? "bg-warn-surface border-warn/30"
                      : "bg-danger-surface border-danger/30"
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    {checkPass ? (
                      <CheckCircle className="h-4 w-4 text-accent shrink-0 mt-0.5" />
                    ) : checkWarn ? (
                      <AlertTriangle className="h-4 w-4 text-warn shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="h-4 w-4 text-danger shrink-0 mt-0.5" />
                    )}
                    <div>
                      <span className="font-semibold text-fg block">
                        {check.name}
                      </span>
                      <p className="text-[11px] text-fg-muted mt-0.5">
                        {check.message}
                      </p>
                      {check.suggested_action && (
                        <p className="text-[11px] text-accent font-medium mt-1">
                          ↳ {check.suggested_action}
                        </p>
                      )}
                      {check.details && (check.details.observed || check.details.threshold) && (
                        <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] font-mono">
                          {check.details.observed && (
                            <span className="rounded bg-surface px-1.5 py-0.5 border border-border text-fg-muted">
                              Observed: <strong className="text-fg">{String(check.details.observed)}</strong>
                            </span>
                          )}
                          {check.details.threshold && (
                            <span className="rounded bg-surface px-1.5 py-0.5 border border-border text-fg-muted">
                              Threshold: <strong className="text-fg">{String(check.details.threshold)}</strong>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <span
                    className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-bold border shrink-0 ${
                      checkPass
                        ? "bg-accent-surface text-accent border-accent/20"
                        : checkWarn
                        ? "bg-warn text-white border-warn"
                        : "bg-danger text-white border-danger"
                    }`}
                  >
                    {check.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* 6. Warning Acknowledgement Checkbox (Required for WARN state) */}
        {isWarn && (
          <div className="rounded-xl border border-warn/40 bg-warn-surface p-4">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={acknowledgedWarning}
                onChange={(e) => setAcknowledgedWarning(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-warn text-accent focus:ring-accent"
              />
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-fg block">
                  I understand this trade exceeds my {concentrationThreshold}% concentration guideline.
                </span>
                <span className="text-[11px] text-fg-muted block">
                  TradeGuard requires explicit human acknowledgement before proceeding with warning-flagged orders.
                </span>
              </div>
            </label>
          </div>
        )}

        {/* 7. BLOCK Explanation and 1-Click Safe Amount Suggestion */}
        {isBlock && (
          <div className="rounded-xl border border-danger/30 bg-danger-surface p-4 space-y-2">
            <div className="flex items-center gap-2 text-danger font-semibold text-xs">
              <Lock className="h-4 w-4" />
              <span>Why execution is blocked</span>
            </div>
            <p className="text-xs text-danger-text">
              {proposal.risk.block_reason || "This order violates server-enforced safety guardrails and cannot be executed."}
            </p>
            {proposal.risk.suggested_safe_amount_usd && proposal.risk.suggested_safe_amount_usd > 0 && (
              <div className="pt-2">
                <button
                  type="button"
                  disabled={refreshing}
                  onClick={async () => {
                    const safeAmt = proposal.risk.suggested_safe_amount_usd;
                    if (safeAmt) {
                      try {
                        setRefreshing(true);
                        setErrorMessage(null);
                        const sideVerb = proposal.side === "BUY" ? "Buy" : "Sell";
                        const newPrompt = `${sideVerb} $${safeAmt} of ${proposal.asset}`;
                        const refreshed = await api.createProposal(newPrompt);
                        if (onRefreshQuote) onRefreshQuote(refreshed);
                      } catch (err: any) {
                        setErrorMessage(err.message || "Failed to adjust order to safe amount.");
                      } finally {
                        setRefreshing(false);
                      }
                    }
                  }}
                  className="rounded-lg bg-surface border border-danger/30 px-3 py-1.5 text-xs font-semibold text-fg hover:border-accent transition-colors flex items-center gap-1.5"
                >
                  <span>Reduce order to safe limit: ${proposal.risk.suggested_safe_amount_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })} USD</span>
                  <ArrowRight className="h-3.5 w-3.5 text-accent" />
                </button>
              </div>
            )}
          </div>
        )}

        {errorMessage && (
          <div role="alert" className="rounded-xl border border-danger/30 bg-danger-surface p-3.5 text-xs text-danger font-medium flex items-center gap-2">
            <span>{errorMessage}</span>
          </div>
        )}

        {/* 8. Action Decision Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-border">
          <button
            type="button"
            onClick={handleCancel}
            disabled={cancelling || confirming}
            className="w-full sm:w-auto min-h-[44px] px-4 py-2.5 text-xs font-medium text-fg-muted hover:text-fg hover:bg-canvas-subtle rounded-xl transition-all focus-visible:ring-2 focus-visible:ring-accent"
          >
            Cancel Review
          </button>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {isExpired ? (
              <button
                type="button"
                onClick={handleRefresh}
                disabled={refreshing}
                className="w-full sm:w-auto min-h-[44px] rounded-xl bg-accent px-5 py-2.5 text-xs font-bold text-slate-950 hover:bg-accent-dark transition-all flex items-center justify-center gap-2 shadow-subtle focus-visible:ring-2 focus-visible:ring-accent"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
                <span>Refresh Expired Quote</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleConfirm}
                disabled={!canExecute || confirming || (isWarn && !acknowledgedWarning) || isExpired}
                className={`w-full sm:w-auto min-h-[44px] rounded-xl px-6 py-2.5 text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-subtle focus-visible:ring-2 focus-visible:ring-accent ${
                  !canExecute || (isWarn && !acknowledgedWarning)
                    ? "bg-fg-muted/40 text-fg-muted cursor-not-allowed opacity-60"
                    : isWarn
                    ? "bg-warn text-slate-950 hover:bg-warn/90"
                    : "bg-accent text-slate-950 hover:bg-accent-dark"
                }`}
              >
                {confirming ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-950 border-t-transparent" />
                    <span>Confirming...</span>
                  </>
                ) : (
                  <>
                    <Lock className="h-3.5 w-3.5" />
                    <span>{isDemo ? "Confirm simulated trade" : "Confirm trade"}</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
