"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  createChart,
  CandlestickSeries,
  ColorType,
  LineStyle,
  IChartApi,
  ISeriesApi,
} from "lightweight-charts";
import { MarketCandlesResponse, TradeProposal } from "@/lib/types";
import { api } from "@/lib/api";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  AlertCircle,
  RefreshCw,
  Activity,
  Layers,
} from "lucide-react";

interface MarketContextChartProps {
  initialAsset?: string;
  activeProposal?: TradeProposal | null;
  onSelectAsset?: (asset: string) => void;
  className?: string;
}

const SUPPORTED_ASSETS = ["BTC", "ETH", "SOL", "USDC"];
const TIMEFRAMES = [
  { label: "1H", window: "1h", resolution: "1m" },
  { label: "4H", window: "4h", resolution: "5m" },
  { label: "1D", window: "1d", resolution: "15m" },
  { label: "7D", window: "7d", resolution: "1h" },
];

export function MarketContextChart({
  initialAsset = "BTC",
  activeProposal,
  onSelectAsset,
  className = "",
}: MarketContextChartProps) {
  const [selectedAsset, setSelectedAsset] = useState<string>(
    activeProposal?.asset || initialAsset
  );
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("1D");
  const [marketData, setMarketData] = useState<MarketCandlesResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Sync selected asset when proposal changes or initialAsset changes
  useEffect(() => {
    if (activeProposal?.asset) {
      setSelectedAsset(activeProposal.asset);
    } else if (initialAsset && initialAsset !== selectedAsset) {
      setSelectedAsset(initialAsset);
    }
  }, [activeProposal?.asset, initialAsset, selectedAsset]);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const priceLineRef = useRef<any>(null);

  // References to read latest proposal and asset inside chart autoscale callback
  const activeProposalRef = useRef(activeProposal);
  activeProposalRef.current = activeProposal;
  const selectedAssetRef = useRef(selectedAsset);
  selectedAssetRef.current = selectedAsset;

  // Detect current theme (dark or light)
  const isDark = useCallback(() => {
    if (typeof document === "undefined") return true;
    return document.documentElement.classList.contains("dark");
  }, []);

  // Fetch candle data from backend True Markets adapter
  const fetchCandles = useCallback(
    async (assetToFetch: string, tfLabel: string) => {
      const tf = TIMEFRAMES.find((t) => t.label === tfLabel) || TIMEFRAMES[2];
      try {
        setLoading(true);
        setError(null);
        const data = await api.getMarketCandles(
          assetToFetch,
          tf.window,
          tf.resolution
        );
        setMarketData(data);
      } catch (err: any) {
        console.error("Failed to load candles:", err);
        setError(err.message || "Market data temporarily unavailable");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchCandles(selectedAsset, selectedTimeframe);
  }, [selectedAsset, selectedTimeframe, fetchCandles]);

  // Initialize or update the lightweight-charts instance
  useEffect(() => {
    if (!containerRef.current) return;

    const dark = isDark();
    const bgColor = "transparent";
    const textColor = dark ? "#94a3b8" : "#64748b";
    const gridColor = dark ? "rgba(255, 255, 255, 0.04)" : "rgba(0, 0, 0, 0.04)";
    const borderColor = dark ? "#222b3b" : "#e2e8f0";
    const upColor = dark ? "#14b8a6" : "#0d9488"; // Institutional teal
    const downColor = dark ? "#ef4444" : "#dc2626";

    // Clean up previous chart instance
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
      seriesRef.current = null;
      priceLineRef.current = null;
    }

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: bgColor },
        textColor,
        fontFamily: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: gridColor },
        horzLines: { color: gridColor },
      },
      crosshair: {
        vertLine: {
          color: dark ? "#334155" : "#cbd5e1",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: dark ? "#1e2636" : "#0f172a",
        },
        horzLine: {
          color: dark ? "#334155" : "#cbd5e1",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: dark ? "#1e2636" : "#0f172a",
        },
      },
      rightPriceScale: {
        borderColor,
        visible: true,
        scaleMargins: {
          top: 0.12,
          bottom: 0.12,
        },
      },
      timeScale: {
        borderColor,
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: {
        vertTouchDrag: false,
      },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor,
      downColor,
      borderVisible: false,
      wickUpColor: upColor,
      wickDownColor: downColor,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    // Handle responsive container resizing
    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    const resizeObserver = new ResizeObserver(() => handleResize());
    resizeObserver.observe(containerRef.current);
    handleResize();

    // Listen to theme mutations on documentElement
    const observer = new MutationObserver(() => {
      const isNowDark = isDark();
      chart.applyOptions({
        layout: {
          textColor: isNowDark ? "#94a3b8" : "#64748b",
        },
        grid: {
          vertLines: { color: isNowDark ? "rgba(255, 255, 255, 0.04)" : "rgba(0, 0, 0, 0.04)" },
          horzLines: { color: isNowDark ? "rgba(255, 255, 255, 0.04)" : "rgba(0, 0, 0, 0.04)" },
        },
        rightPriceScale: {
          borderColor: isNowDark ? "#222b3b" : "#e2e8f0",
        },
        timeScale: {
          borderColor: isNowDark ? "#222b3b" : "#e2e8f0",
        },
      });
      series.applyOptions({
        upColor: isNowDark ? "#14b8a6" : "#0d9488",
        wickUpColor: isNowDark ? "#14b8a6" : "#0d9488",
      });
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });

    return () => {
      resizeObserver.disconnect();
      observer.disconnect();
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        seriesRef.current = null;
      }
    };
  }, [isDark]);

  // Update candle data in chart series
  useEffect(() => {
    if (!seriesRef.current) return;

    if (!marketData?.candles || marketData.candles.length === 0) {
      try {
        seriesRef.current.setData([]);
      } catch {}
      return;
    }

    try {
      const candleData = marketData.candles.map((c) => ({
        time: c.time as any,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));
      seriesRef.current.setData(candleData);
      chartRef.current?.timeScale().fitContent();
    } catch (err) {
      console.warn("Could not apply candle series data:", err);
    }
  }, [marketData]);

  // Manage proposed trade entry horizontal line marker
  useEffect(() => {
    if (!seriesRef.current) return;

    // Remove existing price line if any
    if (priceLineRef.current) {
      try {
        seriesRef.current.removePriceLine(priceLineRef.current);
      } catch {}
      priceLineRef.current = null;
    }

    // Only add marker if active proposal matches current asset
    if (activeProposal && activeProposal.asset === selectedAsset && activeProposal.quote) {
      const rawPrice =
        activeProposal.side === "BUY"
          ? (activeProposal.quote.ask ?? activeProposal.quote.mid)
          : (activeProposal.quote.bid ?? activeProposal.quote.mid);
      const entryPrice = typeof rawPrice === "number" && rawPrice > 0 ? rawPrice : null;

      if (entryPrice !== null) {
        try {
          const line = seriesRef.current.createPriceLine({
            price: entryPrice,
            color: "#06b6d4", // Restrained cyan/teal
            lineWidth: 2,
            lineStyle: LineStyle.Dashed,
            axisLabelVisible: true,
            title: `Proposed Entry ($${entryPrice.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: entryPrice < 10 ? 4 : 2,
            })})`,
          });
          priceLineRef.current = line;
          chartRef.current?.priceScale("right").applyOptions({ autoScale: true });
        } catch (e) {
          console.warn("Failed to create proposed trade price line:", e);
        }
      }
    }
  }, [activeProposal, selectedAsset, marketData]);

  const handleAssetChange = (asset: string) => {
    setSelectedAsset(asset);
    if (onSelectAsset) onSelectAsset(asset);
  };

  const isUp = (marketData?.price_change ?? 0) >= 0;
  const isAvailable = marketData?.is_available ?? false;

  return (
    <div
      className={`rounded-2xl border border-border bg-surface p-4 sm:p-5 shadow-card precision-rail flex flex-col justify-between transition-all ${className}`}
    >
      {/* 1. Header Bar: Asset Info + Controls */}
      <div className="flex flex-col gap-3 pb-3 border-b border-border">
        {/* Top Row: Asset Switcher + Timeframe Pills */}
        <div className="flex flex-wrap items-center justify-between gap-2.5">
          {/* Asset Tabs */}
          <div className="flex items-center gap-1 rounded-xl bg-canvas-subtle p-1 border border-border">
            {SUPPORTED_ASSETS.map((asset) => {
              const isSelected = selectedAsset === asset;
              const hasProposal = activeProposal?.asset === asset;
              return (
                <button
                  key={asset}
                  type="button"
                  onClick={() => handleAssetChange(asset)}
                  className={`relative px-2.5 py-1 text-xs font-mono font-semibold rounded-lg transition-all ${
                    isSelected
                      ? "bg-surface text-fg shadow-subtle border border-border/80"
                      : "text-fg-subtle hover:text-fg hover:bg-surface/50"
                  }`}
                >
                  <span>{asset}</span>
                  {hasProposal && (
                    <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-cyan-500 animate-pulse" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Timeframe Selector */}
          <div className="flex items-center gap-1 rounded-xl bg-canvas-subtle p-1 border border-border">
            {TIMEFRAMES.map((tf) => {
              const isSelected = selectedTimeframe === tf.label;
              return (
                <button
                  key={tf.label}
                  type="button"
                  onClick={() => setSelectedTimeframe(tf.label)}
                  className={`px-2 py-1 text-[11px] font-mono font-medium rounded-lg transition-all ${
                    isSelected
                      ? "bg-accent text-slate-950 font-bold shadow-subtle"
                      : "text-fg-subtle hover:text-fg"
                  }`}
                >
                  {tf.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Second Row: Asset Price, Delta & Range Stats */}
        <div className="flex flex-wrap items-baseline justify-between gap-3 pt-1">
          <div className="flex items-baseline gap-2.5">
            <span className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-fg tabular-nums">
              {typeof marketData?.current_price === "number"
                ? `$${marketData.current_price.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: marketData.current_price < 10 ? 4 : 2,
                  })}`
                : "—"}
            </span>

            {typeof marketData?.price_change === "number" && typeof marketData?.price_change_pct === "number" && (
              <div
                className={`inline-flex items-center gap-1 text-xs font-mono font-semibold ${
                  isUp ? "text-accent" : "text-danger"
                }`}
              >
                {isUp ? (
                  <TrendingUp className="h-3.5 w-3.5" />
                ) : (
                  <TrendingDown className="h-3.5 w-3.5" />
                )}
                <span>
                  {isUp ? "+" : ""}
                  {marketData.price_change_pct}%
                </span>
                <span className="text-fg-subtle font-normal text-[11px]">
                  ({isUp ? "+" : ""}${marketData.price_change.toLocaleString(undefined, { minimumFractionDigits: 2 })})
                </span>
              </div>
            )}
          </div>

          {/* 24H Range & Freshness */}
          <div className="flex items-center gap-3 text-[11px] font-mono text-fg-subtle">
            {typeof marketData?.high === "number" && typeof marketData?.low === "number" && (
              <div className="hidden sm:flex items-center gap-2">
                <span>
                  24H H: <strong className="text-fg">${marketData.high.toLocaleString()}</strong>
                </span>
                <span>·</span>
                <span>
                  24H L: <strong className="text-fg">${marketData.low.toLocaleString()}</strong>
                </span>
              </div>
            )}

            {/* Freshness Badge */}
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-canvas-subtle border border-border">
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isAvailable
                    ? "bg-accent animate-pulse"
                    : "bg-warn"
                }`}
              />
              <span className="text-[10px] text-fg-muted font-medium">
                {marketData?.status_label || "Connecting..."}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Chart Viewport / Skeleton / Fallback State */}
      <div className="relative w-full h-[280px] sm:h-[320px] my-2">
        {/* Actual Canvas Container */}
        <div
          ref={containerRef}
          className={`w-full h-full ${!isAvailable && !loading ? "opacity-20 pointer-events-none" : ""}`}
        />

        {/* Loading Overlay */}
        {loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface/60 backdrop-blur-xs rounded-xl text-xs font-mono text-fg-subtle space-y-2 z-10">
            <RefreshCw className="h-5 w-5 animate-spin text-accent" />
            <span>Loading True Markets OHLC data...</span>
          </div>
        )}

        {/* Error / Unavailable Fallback (No Fake Candles!) */}
        {!loading && (!isAvailable || error) && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-surface/85 backdrop-blur-xs rounded-xl border border-border/80 z-20 space-y-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-warn-surface border border-warn/30 text-warn">
              <AlertCircle className="h-5 w-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-fg uppercase font-mono tracking-wide">
                Market Data Temporarily Unavailable
              </h4>
              <p className="text-[11px] text-fg-subtle max-w-sm mt-1 leading-relaxed">
                Could not retrieve candle series from True Markets for {selectedAsset}. Pre-trade risk validation and execution guardrails remain fully authoritative and unaffected.
              </p>
            </div>
            <button
              type="button"
              onClick={() => fetchCandles(selectedAsset, selectedTimeframe)}
              className="mt-1 px-3 py-1.5 rounded-lg border border-border bg-canvas-subtle text-xs font-mono font-medium text-fg-muted hover:text-fg hover:bg-surface transition-colors flex items-center gap-1.5 shadow-subtle"
            >
              <RefreshCw className="h-3 w-3" />
              <span>Retry Market Feed</span>
            </button>
          </div>
        )}
      </div>

      {/* 3. Footer Context Strip: Connects Market Context to Risk & Intent */}
      <div className="pt-2.5 border-t border-border flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-fg-subtle">
        <div className="flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-accent" />
          <span>True Markets OHLC Feed</span>
          <span className="text-fg-muted">({selectedAsset} / {selectedTimeframe} · {TIMEFRAMES.find(t => t.label === selectedTimeframe)?.resolution})</span>
        </div>

        {activeProposal && activeProposal.asset === selectedAsset && typeof (activeProposal.quote?.ask ?? activeProposal.quote?.mid) === "number" ? (
          <div className="flex items-center gap-1.5 text-cyan-400 font-semibold bg-cyan-500/10 px-2 py-0.5 rounded-md border border-cyan-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span>
              Proposed Entry Line: ${(
                activeProposal.side === "BUY"
                  ? (activeProposal.quote.ask ?? activeProposal.quote.mid)
                  : (activeProposal.quote.bid ?? activeProposal.quote.mid)
              ).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
          </div>
        ) : activeProposal ? (
          <button
            type="button"
            onClick={() => handleAssetChange(activeProposal.asset)}
            className="flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 transition-colors text-[11px] underline underline-offset-2"
          >
            <span>Switch to {activeProposal.asset} to view proposed entry line →</span>
          </button>
        ) : (
          <span className="text-fg-subtle">
            AI interprets · Backend validates · User decides
          </span>
        )}
      </div>
    </div>
  );
}
