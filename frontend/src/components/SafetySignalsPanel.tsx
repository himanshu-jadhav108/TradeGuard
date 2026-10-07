"use client";

import React, { useEffect, useState } from "react";
import { SafetySignalsReport } from "@/lib/types";
import { api } from "@/lib/api";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Clock,
  Layers,
  Activity,
  CheckCircle2,
} from "lucide-react";

interface SafetySignalsPanelProps {
  refreshTrigger?: number;
}

export function SafetySignalsPanel({ refreshTrigger }: SafetySignalsPanelProps) {
  const [report, setReport] = useState<SafetySignalsReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSafetySignals();
      setReport(data);
    } catch (err: any) {
      console.error("Failed to load safety signals:", err);
      setError(err.message || "Failed to load safety signals");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, [refreshTrigger]);

  const getSignalIcon = (severity: string, count: number) => {
    if (count === 0 || severity === "INFO") {
      return <CheckCircle2 className="h-4 w-4 text-accent" />;
    }
    if (severity === "WARN") {
      return <AlertTriangle className="h-4 w-4 text-warn" />;
    }
    return <ShieldAlert className="h-4 w-4 text-danger" />;
  };

  const getSeverityBadge = (severity: string, count: number) => {
    if (count === 0 || severity === "INFO") {
      return {
        label: "Normal",
        style: "bg-accent-surface text-accent border-accent/20",
      };
    }
    if (severity === "WARN") {
      return {
        label: "Attention",
        style: "bg-warn-surface text-warn border-warn/20",
      };
    }
    return {
      label: "Elevated",
      style: "bg-danger-surface text-danger border-danger/20",
    };
  };

  const formatFullDateTime = (isoString?: string) => {
    if (!isoString) return "—";
    try {
      const d = new Date(isoString);
      return d.toISOString().replace("T", " ").substring(0, 19) + " UTC";
    } catch {
      return isoString;
    }
  };

  return (
    <div className="w-full rounded-2xl border border-border bg-surface p-5 sm:p-6 shadow-card">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-fg flex items-center gap-2">
              <Activity className="h-4 w-4 text-accent" />
              <span>Safety Signals</span>
            </h3>
            <span className="rounded-full bg-accent-surface px-2.5 py-0.5 text-[10px] font-mono font-semibold text-accent border border-accent/20">
              rule-based safety signals
            </span>
          </div>
          <p className="text-xs text-fg-subtle mt-1">
            Deterministic heuristics calculated exclusively from stored session audit logs
          </p>
        </div>

        <button
          type="button"
          onClick={fetchSignals}
          disabled={loading}
          className="self-start sm:self-center flex items-center gap-1.5 rounded-lg border border-border bg-canvas-subtle px-2.5 py-1 text-xs text-fg-muted hover:text-fg hover:bg-surface transition-colors shadow-subtle"
        >
          <RefreshCw
            className={`h-3 w-3 ${loading ? "animate-spin text-accent" : ""}`}
          />
          <span className="text-xs">Refresh Signals</span>
        </button>
      </div>

      {/* Content */}
      {loading && !report ? (
        <div className="py-8 text-center text-xs text-fg-subtle">
          <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-accent" />
          <span>Computing safety signals from audit log...</span>
        </div>
      ) : error && !report ? (
        <div className="py-6 text-center text-xs text-danger">
          <AlertTriangle className="h-5 w-5 mx-auto mb-1 text-danger" />
          <span>{error}</span>
        </div>
      ) : !report || report.signals.length === 0 ? (
        <div className="py-6 text-center text-xs text-fg-subtle">
          No signal data available.
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {report.signals.map((sig) => {
              const badge = getSeverityBadge(sig.severity, sig.count);
              return (
                <div
                  key={sig.id}
                  className="rounded-xl border border-border bg-canvas-subtle p-3.5 flex flex-col justify-between hover:border-accent/30 transition-colors"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5">
                        {getSignalIcon(sig.severity, sig.count)}
                        <span className="font-semibold text-xs text-fg line-clamp-1">
                          {sig.name}
                        </span>
                      </div>
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-mono font-medium border ${badge.style}`}
                      >
                        {badge.label}
                      </span>
                    </div>
                    <p className="text-[11px] text-fg-subtle leading-tight line-clamp-2">
                      {sig.description}
                    </p>
                  </div>

                  <div className="mt-3 pt-2 border-t border-border flex items-baseline justify-between">
                    <span className="text-[10px] font-mono text-fg-muted uppercase tracking-wider">
                      Count
                    </span>
                    <span
                      className={`text-lg font-bold font-mono ${
                        sig.count > 0 && sig.severity !== "INFO"
                          ? sig.severity === "CRITICAL"
                            ? "text-danger"
                            : "text-warn"
                          : "text-fg"
                      }`}
                    >
                      {sig.count}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer Metadata */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-border text-[11px] text-fg-subtle font-mono">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <Layers className="h-3 w-3 text-fg-muted" />
                <span>Events Evaluated:</span>
                <strong className="text-fg font-semibold">
                  {report.total_stored_events}
                </strong>
              </span>
              <span>·</span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3 text-fg-muted" />
                <span>Computed:</span>
                <span className="text-fg">{formatFullDateTime(report.computed_at)}</span>
              </span>
            </div>

            <div className="text-[10px] text-fg-muted">
              Source: Scoped SQLite Audit Log · 100% Deterministic
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
