"use client";

import React, { useEffect, useState } from "react";
import { PortfolioSummary } from "@/lib/types";
import { api } from "@/lib/api";
import { Wallet, DollarSign, Activity, RefreshCw, AlertCircle } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const ASSET_COLORS: Record<string, string> = {
  BTC: "#f59e0b",
  ETH: "#6366f1",
  SOL: "#14b8a6",
  USDC: "#0d9488",
  CASH: "#0f766e",
};

export function PortfolioOverview({ refreshTrigger }: { refreshTrigger?: number }) {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPortfolio();
      setPortfolio(data);
    } catch (e: any) {
      console.error("Failed to load portfolio:", e);
      setError(e.message || "Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, [refreshTrigger]);

  if (loading && !portfolio) {
    return (
      <div className="w-full rounded-2xl border border-border bg-surface p-8 text-center text-fg-muted">
        <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-accent" />
        <span className="text-xs">Loading portfolio balances...</span>
      </div>
    );
  }

  if (error && !portfolio) {
    return (
      <div className="w-full rounded-2xl border border-danger/30 bg-surface p-8 text-center text-fg-muted space-y-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-danger-surface text-danger mx-auto border border-danger/30">
          <AlertCircle className="h-5 w-5" />
        </div>
        <p className="text-sm font-semibold text-fg">Portfolio Unavailable</p>
        <p className="text-xs text-fg-subtle max-w-sm mx-auto">
          Could not connect to the TradeGuard backend service to load current balances.
        </p>
        <button
          type="button"
          onClick={fetchPortfolio}
          className="rounded-xl bg-accent px-4 py-2 min-h-[44px] text-xs font-bold text-slate-950 hover:bg-accent-dark transition-all inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-accent"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Retry</span>
        </button>
      </div>
    );
  }

  if (!portfolio) {
    return null;
  }

  const totalPositions = portfolio.positions.length;
  const cashPct = portfolio.total_value_usd > 0
    ? ((portfolio.cash_usd / portfolio.total_value_usd) * 100).toFixed(1)
    : "0.0";

  // Prepare chart data
  const chartData = [
    {
      name: "Cash (USDC)",
      value: portfolio.cash_usd,
      color: ASSET_COLORS.CASH,
    },
    ...portfolio.positions.map((p) => ({
      name: p.asset,
      value: p.value_usd,
      color: ASSET_COLORS[p.asset] || "#64748b",
    })),
  ];

  // Custom high-contrast tooltip for Recharts
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const assetColor = data.payload?.color || "#0d9488";
      const totalVal = portfolio?.total_value_usd || 1;
      const sharePct = ((Number(data.value) / totalVal) * 100).toFixed(1);

      return (
        <div className="rounded-xl border border-border-strong bg-surface-elevated p-3 shadow-elevated text-xs font-mono pointer-events-none min-w-[150px]">
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className="h-2.5 w-2.5 rounded-full shrink-0"
              style={{ backgroundColor: assetColor }}
            />
            <span className="font-sans font-semibold text-fg text-xs">
              {data.name}
            </span>
          </div>
          <div className="text-fg font-bold text-sm tabular-nums">
            ${Number(data.value).toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
          <div className="text-[11px] text-fg-muted mt-0.5 font-sans font-medium">
            {sharePct}% of portfolio
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Total Net Worth */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-fg-muted mb-1.5">
            <span className="text-xs font-medium">Total Portfolio Valuation</span>
            <Wallet className="h-4 w-4 text-accent" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-fg tabular-nums font-sans">
            $
            {portfolio.total_value_usd.toLocaleString(undefined, {
              minimumFractionDigits: 2,
            })}
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-fg-muted font-mono">
            <span>{totalPositions} open asset holdings</span>
          </div>
        </div>

        {/* Available Cash */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-fg-muted mb-1.5">
            <span className="text-xs font-medium">Liquid Cash (USDC)</span>
            <DollarSign className="h-4 w-4 text-accent" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-fg tabular-nums font-sans">
            $
            {portfolio.cash_usd.toLocaleString(undefined, {
              minimumFractionDigits: 2,
            })}
          </div>
          <span className="mt-2 block text-xs text-fg-muted font-mono">
            {cashPct}% of total purchasing power
          </span>
        </div>

        {/* Execution Mode */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-fg-muted mb-1.5">
            <span className="text-xs font-medium">Environment Mode</span>
            <Activity className="h-4 w-4 text-accent" />
          </div>
          <div className="text-xl font-bold tracking-tight text-fg flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
            <span className="font-mono text-sm">{portfolio.mode}</span>
            <span className="text-xs font-normal text-fg-subtle">
              ({portfolio.mode === "UAT" ? "True Markets UAT" : "Simulated Demo"})
            </span>
          </div>
          <span className="mt-2 block text-xs text-fg-muted font-mono text-[11px]">
            Deterministic risk validation enforced
          </span>
        </div>
      </div>

      {/* Allocation Breakdown and Holdings Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Allocation Donut Chart */}
        <div className="lg:col-span-4 rounded-2xl border border-border bg-surface p-5 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-fg font-sans">
              Asset Exposure
            </h3>
            <span className="font-mono text-[11px] text-fg-muted font-medium">
              100% Total
            </span>
          </div>

          <div className="h-52 w-full my-auto">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="var(--color-surface)"
                  strokeWidth={2}
                  style={{ outline: "none" }}
                >
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      style={{ outline: "none" }}
                    />
                  ))}
                </Pie>
                <Tooltip
                  content={<CustomTooltip />}
                  wrapperStyle={{ outline: "none" }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-3 border-t border-border text-[11px]">
            {chartData.map((d) => (
              <div key={d.name} className="flex items-center gap-1.5">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: d.color }}
                />
                <span className="text-fg font-medium">{d.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Positions Table */}
        <div className="lg:col-span-8 rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-fg font-sans">
              Settled Positions
            </h3>
            <span className="text-[11px] font-mono text-fg-muted">
              Updated: {new Date(portfolio.as_of).toLocaleTimeString()}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-border text-fg-muted text-[11px] font-sans">
                  <th className="pb-3 font-semibold">Asset</th>
                  <th className="pb-3 font-semibold">Quantity</th>
                  <th className="pb-3 font-semibold">Reference Price</th>
                  <th className="pb-3 font-semibold">Total Value</th>
                  <th className="pb-3 font-semibold">Allocation</th>
                  <th className="pb-3 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {portfolio.positions.map((pos) => (
                  <tr key={pos.asset} className="hover:bg-surface-hover/50 transition-colors">
                    <td className="py-3 font-sans font-semibold text-fg flex items-center gap-2">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{
                          backgroundColor:
                            ASSET_COLORS[pos.asset] || "#0d9488",
                        }}
                      />
                      <span>{pos.asset}</span>
                    </td>
                    <td className="py-3 text-fg font-medium tabular-nums">
                      {pos.quantity.toLocaleString(undefined, {
                        maximumFractionDigits: 6,
                      })}
                    </td>
                    <td className="py-3 text-fg tabular-nums">
                      $
                      {pos.price_usd.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                      })}
                    </td>
                    <td className="py-3 font-bold text-fg tabular-nums">
                      $
                      {pos.value_usd.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                      })}
                    </td>
                    <td className="py-3 text-fg font-medium">
                      <div className="flex items-center gap-2">
                        <span className="tabular-nums">{pos.allocation_pct}%</span>
                        <div className="h-1.5 w-12 bg-border rounded-full overflow-hidden">
                          <div
                            className="h-full bg-accent rounded-full"
                            style={{ width: `${Math.min(100, pos.allocation_pct)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 text-right font-mono text-[11px] text-accent">
                      Settled
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
