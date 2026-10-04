"use client";

import React, { useEffect, useState } from "react";
import { AuditEvent } from "@/lib/types";
import { api } from "@/lib/api";
import {
  ShieldCheck,
  FileText,
  CheckCircle2,
  Clock,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

export function ActivityTimeline({ refreshTrigger }: { refreshTrigger?: number }) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchActivity = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getActivity(50);
      setEvents(data);
    } catch (e: any) {
      console.error("Failed to load activity:", e);
      setError(e.message || "Failed to load activity log");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivity();
  }, [refreshTrigger]);

  const getEventBadge = (type: string) => {
    switch (type) {
      case "ORDER_FILLED":
      case "TRADE_CONFIRMED":
        return {
          icon: <CheckCircle2 className="h-3.5 w-3.5 text-accent" />,
          style: "bg-accent-surface text-accent border-accent/20",
        };
      case "PROPOSAL_CREATED":
        return {
          icon: <FileText className="h-3.5 w-3.5 text-warn" />,
          style: "bg-warn-surface text-warn border-warn/20",
        };
      case "ACCOUNT_SEEDED":
      case "ACCOUNT_RESET":
        return {
          icon: <ShieldCheck className="h-3.5 w-3.5 text-fg-muted" />,
          style: "bg-canvas-subtle text-fg-muted border-border",
        };
      default:
        return {
          icon: <Clock className="h-3.5 w-3.5 text-fg-subtle" />,
          style: "bg-canvas-subtle text-fg-subtle border-border",
        };
    }
  };

  return (
    <div className="w-full rounded-2xl border border-border bg-surface p-5 sm:p-6 shadow-card">
      <div className="flex items-center justify-between mb-6 pb-3 border-b border-border">
        <div>
          <h3 className="text-sm font-semibold text-fg">
            TradeGuard Activity Log
          </h3>
          <p className="text-xs text-fg-subtle mt-0.5">
            Chronological record of intent interpretations, risk checks, and trade confirmations
          </p>
        </div>
        <button
          type="button"
          suppressHydrationWarning
          onClick={fetchActivity}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-border bg-canvas-subtle px-2.5 py-1 text-xs text-fg-muted hover:text-fg hover:bg-surface transition-colors shadow-subtle"
        >
          <RefreshCw
            className={`h-3 w-3 ${loading ? "animate-spin text-accent" : ""}`}
          />
          <span className="text-xs">Refresh</span>
        </button>
      </div>

      {loading && events.length === 0 ? (
        <div className="py-12 text-center text-xs text-fg-subtle">
          <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-accent" />
          <span>Loading activity log...</span>
        </div>
      ) : error && events.length === 0 ? (
        <div className="py-10 text-center text-xs text-fg-muted space-y-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-danger-surface text-danger mx-auto border border-danger/30">
            <AlertCircle className="h-4 w-4" />
          </div>
          <p className="text-sm font-semibold text-fg">Activity Log Unavailable</p>
          <p className="text-xs text-fg-subtle max-w-sm mx-auto">
            Could not connect to the TradeGuard backend service to retrieve session activity.
          </p>
          <button
            type="button"
            onClick={fetchActivity}
            className="rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white hover:bg-accent-dark transition-all inline-flex items-center gap-1.5"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Retry</span>
          </button>
        </div>
      ) : events.length === 0 ? (
        <div className="py-12 text-center text-xs text-fg-subtle">
          No activity recorded yet for this session. Submit a trade intent above to initiate the log.
        </div>
      ) : (
        <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-px before:bg-border">
          {events.map((evt) => {
            const isExpanded = expandedId === evt.id;
            const badge = getEventBadge(evt.event_type);
            const prompt = evt.metadata?.raw_prompt;

            return (
              <div key={evt.id} className="relative group">
                {/* Timeline node */}
                <div className="absolute -left-6 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-surface border border-border shadow-subtle group-hover:border-accent transition-colors">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                </div>

                <div className="rounded-xl border border-border bg-canvas-subtle p-3.5 transition-all hover:border-accent/40">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-bold border flex items-center gap-1 ${badge.style}`}
                      >
                        {badge.icon}
                        <span>{evt.event_type}</span>
                      </span>

                      {evt.proposal_id && (
                        <span className="font-mono text-[10px] text-fg-subtle">
                          {evt.proposal_id}
                        </span>
                      )}
                    </div>

                    <time className="font-mono text-[11px] text-fg-subtle">
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </time>
                  </div>

                  <p className="mt-2 text-xs text-fg font-sans leading-relaxed">
                    {evt.summary}
                  </p>

                  {prompt && (
                    <div className="mt-2 p-2 rounded-lg bg-surface border border-border text-[11px] font-mono text-fg-muted">
                      <span className="text-fg-subtle block text-[10px] font-sans">User Intent:</span>
                      “{prompt}”
                    </div>
                  )}

                  {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                    <div className="mt-2">
                      <button
                        type="button"
                        onClick={() => setExpandedId(isExpanded ? null : evt.id)}
                        className="text-[11px] text-fg-subtle hover:text-fg transition-colors flex items-center gap-1 font-mono"
                      >
                        <span>{isExpanded ? "Hide details" : "View parameters"}</span>
                        {isExpanded ? (
                          <ChevronUp className="h-3 w-3" />
                        ) : (
                          <ChevronDown className="h-3 w-3" />
                        )}
                      </button>

                      {isExpanded && (
                        <pre className="mt-2 rounded-lg bg-surface border border-border p-3 text-[10px] font-mono text-fg-muted overflow-x-auto">
                          {JSON.stringify(evt.metadata, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
