"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { PortfolioSummary } from "@/lib/types";
import { api } from "@/lib/api";
import { Wallet, DollarSign, PieChart, ArrowRight, RefreshCw, AlertCircle } from "lucide-react";

interface PortfolioContextStripProps {
  refreshTrigger?: number;
}

export function PortfolioContextStrip({ refreshTrigger }: PortfolioContextStripProps) {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPortfolio();
      setPortfolio(data);
    } catch (err: any) {
      console.error("Context strip portfolio fetch error:", err);
      setError(err.message || "Failed to load portfolio metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [refreshTrigger]);

  if (loading && !portfolio) {
    return (
      <div className="rounded-xl border border-border bg-surface/80 p-3.5 flex items-center justify-between text-xs text-fg-subtle animate-pulse">
        <div className="flex items-center gap-6">
          <div className="h-4 w-28 bg-canvas-subtle rounded" />
          <div className="h-4 w-28 bg-canvas-subtle rounded" />
          <div className="h-4 w-28 bg-canvas-subtle rounded" />
        </div>
        <div className="h-4 w-20 bg-canvas-subtle rounded" />
      </div>
    );
  }

  if (error && !portfolio) {
    return (
      <div className="rounded-xl border border-danger/25 bg-danger-surface/40 px-4 py-2.5 flex items-center justify-between text-xs text-danger">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-3.5 w-3.5" />
          <span>Portfolio metrics unavailable</span>
        </div>
        <button
          type="button"
          onClick={fetchSummary}
          className="text-xs font-semibold text-accent hover:underline flex items-center gap-1"
        >
          <RefreshCw className="h-3 w-3" />
          <span>Retry</span>
        </button>
      </div>
    );
  }

  if (!portfolio) return null;

  // Calculate highest exposure asset
  const sortedPositions = [...portfolio.positions].sort((a, b) => b.value_usd - a.value_usd);
  const topPosition = sortedPositions[0];
  const topExposurePct =
    topPosition && portfolio.total_value_usd > 0
      ? ((topPosition.value_usd / portfolio.total_value_usd) * 100).toFixed(1)
      : "0.0";

  return (
    <div className="rounded-xl border border-border bg-surface/90 backdrop-blur-sm px-4 py-3 shadow-subtle precision-rail">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Metric Pillars */}
        <div className="grid grid-cols-3 sm:flex sm:items-center gap-4 sm:gap-8 divide-x-0 sm:divide-x divide-border">
          {/* Portfolio Value */}
          <div className="space-y-0.5">
            <span className="text-[10px] font-mono uppercase text-fg-subtle tracking-wider flex items-center gap-1">
              <Wallet className="h-3 w-3 text-accent" />
              <span>Portfolio Value</span>
            </span>
            <div className="text-sm sm:text-base font-bold text-fg tabular-nums font-mono">
              $
              {portfolio.total_value_usd.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
          </div>

          {/* Liquid Cash */}
          <div className="sm:pl-8 space-y-0.5">
            <span className="text-[10px] font-mono uppercase text-fg-subtle tracking-wider flex items-center gap-1">
              <DollarSign className="h-3 w-3 text-accent" />
              <span>Available Cash</span>
            </span>
            <div className="text-sm sm:text-base font-bold text-fg tabular-nums font-mono">
              $
              {portfolio.cash_usd.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
          </div>

          {/* Target Exposure */}
          <div className="sm:pl-8 space-y-0.5">
            <span className="text-[10px] font-mono uppercase text-fg-subtle tracking-wider flex items-center gap-1">
              <PieChart className="h-3 w-3 text-accent" />
              <span>Top Exposure</span>
            </span>
            <div className="text-sm sm:text-base font-bold text-fg font-mono">
              {topPosition ? (
                <>
                  <span>{topPosition.asset} </span>
                  <span
                    className={
                      Number(topExposurePct) > 40 ? "text-warn" : "text-fg-muted"
                    }
                  >
                    {topExposurePct}%
                  </span>
                </>
              ) : (
                <span className="text-fg-subtle">None</span>
              )}
            </div>
          </div>
        </div>

        {/* Navigation Action */}
        <div className="flex items-center justify-between sm:justify-end gap-3 pt-2 md:pt-0 border-t md:border-t-0 border-border">
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-fg-subtle">
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
            <span>{portfolio.mode === "UAT" ? "UAT Execution" : "Simulated Demo"}</span>
          </div>
          <Link
            href="/app/portfolio"
            className="text-xs font-semibold text-accent hover:text-accent-dark transition-colors flex items-center gap-1 group py-1"
          >
            <span>View Portfolio</span>
            <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </div>
    </div>
  );
}
