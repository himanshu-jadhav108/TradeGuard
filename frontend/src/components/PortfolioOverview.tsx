"use client";

import React, { useEffect, useState } from "react";
import { PortfolioSummary } from "@/lib/types";
import { api } from "@/lib/api";
import { Wallet, TrendingUp, DollarSign, PieChart as PieIcon, RefreshCw } from "lucide-react";
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
  USDC: "#10b981",
  CASH: "#059669",
};

export function PortfolioOverview({ refreshTrigger }: { refreshTrigger?: number }) {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      const data = await api.getPortfolio();
      setPortfolio(data);
    } catch (e) {
      console.error("Failed to load portfolio:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, [refreshTrigger]);

  if (loading && !portfolio) {
    return (
      <div className="w-full rounded-2xl border border-border bg-surface p-8 text-center text-fg-subtle">
        <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-emerald" />
        <span>Loading portfolio metrics...</span>
      </div>
    );
  }

  if (!portfolio) {
    return null;
  }

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
      color: ASSET_COLORS[p.asset] || "#8b5cf6",
    })),
  ];

  return (
    <div className="space-y-6">
      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Total Net Worth */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-fg-subtle mb-1">
            <span className="text-xs font-medium">Total Net Worth</span>
            <Wallet className="h-4 w-4 text-emerald" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-fg font-mono">
            $
            {portfolio.total_value_usd.toLocaleString(undefined, {
              minimumFractionDigits: 2,
            })}
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald font-medium">
            <TrendingUp className="h-3.5 w-3.5" />
            <span>+1.94% portfolio 24h</span>
          </div>
        </div>

        {/* Available Cash */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-fg-subtle mb-1">
            <span className="text-xs font-medium">Available Cash (USDC)</span>
            <DollarSign className="h-4 w-4 text-emerald" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-fg font-mono">
            $
            {portfolio.cash_usd.toLocaleString(undefined, {
              minimumFractionDigits: 2,
            })}
          </div>
          <span className="mt-2 block text-xs text-fg-subtle">
            Liquid settled purchasing power
          </span>
        </div>

        {/* Environment & Mode */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between text-fg-subtle mb-1">
            <span className="text-xs font-medium">Execution Mode</span>
            <PieIcon className="h-4 w-4 text-emerald" />
          </div>
          <div className="text-xl font-bold tracking-tight text-fg flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald animate-pulse" />
            <span>{portfolio.mode}</span>
          </div>
          <span className="mt-2 block text-xs text-fg-subtle">
            Seeded simulation with live quote feeds
          </span>
        </div>
      </div>

      {/* Allocation Breakdown and Holdings Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Allocation Pie Chart */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card flex flex-col justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-fg-muted mb-4">
            Asset Exposure
          </h3>
          <div className="h-52 w-full">
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
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: any) => [
                    `$${Number(val).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}`,
                    "Value",
                  ]}
                  contentStyle={{
                    backgroundColor: "var(--color-surface-elevated)",
                    borderColor: "var(--color-border)",
                    borderRadius: "0.5rem",
                    color: "var(--color-fg)",
                    fontSize: "12px",
                  }}
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
                <span className="text-fg-muted font-medium">{d.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Positions Table */}
        <div className="lg:col-span-2 rounded-2xl border border-border bg-surface p-5 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-fg-muted">
              Active Holdings
            </h3>
            <span className="text-xs text-fg-subtle">
              As of {new Date(portfolio.as_of).toLocaleTimeString()}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-border text-fg-subtle text-[11px] font-sans">
                  <th className="pb-3 font-semibold">Asset</th>
                  <th className="pb-3 font-semibold">Quantity</th>
                  <th className="pb-3 font-semibold">Market Price</th>
                  <th className="pb-3 font-semibold">Total Value</th>
                  <th className="pb-3 font-semibold">Allocation</th>
                  <th className="pb-3 font-semibold text-right">24h</th>
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
                            ASSET_COLORS[pos.asset] || "#10b981",
                        }}
                      />
                      <span>{pos.asset}</span>
                    </td>
                    <td className="py-3 text-fg">
                      {pos.quantity.toLocaleString(undefined, {
                        maximumFractionDigits: 6,
                      })}
                    </td>
                    <td className="py-3 text-fg-muted">
                      $
                      {pos.price_usd.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                      })}
                    </td>
                    <td className="py-3 font-semibold text-fg">
                      $
                      {pos.value_usd.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                      })}
                    </td>
                    <td className="py-3 text-fg-muted">
                      <div className="flex items-center gap-2">
                        <span>{pos.allocation_pct}%</span>
                        <div className="h-1.5 w-12 bg-border rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald rounded-full"
                            style={{ width: `${Math.min(100, pos.allocation_pct)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td
                      className={`py-3 text-right font-medium ${
                        pos.pnl_24h_pct >= 0 ? "text-emerald" : "text-danger"
                      }`}
                    >
                      {pos.pnl_24h_pct >= 0 ? "+" : ""}
                      {pos.pnl_24h_pct}%
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
