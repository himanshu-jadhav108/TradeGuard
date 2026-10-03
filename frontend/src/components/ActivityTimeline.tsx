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
} from "lucide-react";

export function ActivityTimeline({ refreshTrigger }: { refreshTrigger?: number }) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchActivity = async () => {
    try {
      setLoading(true);
      const data = await api.getActivity(50);
      setEvents(data);
    } catch (e) {
      console.error("Failed to load activity:", e);
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
            Immutable Audit Trail
          </h3>
          <p className="text-xs text-fg-subtle mt-0.5">
            Cryptographically timestamped record of intent parsing, deterministic checks, and settlements
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
          <span>Loading activity stream...</span>
        </div>
      ) : events.length === 0 ? (
        <div className="py-12 text-center text-xs text-fg-subtle">
          No audit events recorded yet. Submit a trade intent above to initiate the log.
        </div>
      ) : (
        <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-px before:bg-border">
          {events.map((evt) => {
            const isExpanded = expandedId === evt.id;
            const badge = getEventBadge(evt.event_type);
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
                          Prop: {evt.proposal_id.slice(0, 8)}...
                        </span>
                      )}

                      {evt.order_id && (
                        <span className="font-mono text-[10px] text-accent font-semibold">
                          Order: {evt.order_id.slice(0, 12)}
                        </span>
                      )}
                    </div>

                    <span className="font-mono text-[10px] text-fg-subtle tabular-nums">
                      {new Date(evt.timestamp).toLocaleTimeString()} ·{" "}
                      {new Date(evt.timestamp).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="mt-2 text-xs font-medium text-fg">
                    {evt.summary}
                  </p>

                  {/* Metadata Toggle */}
                  {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                    <div className="mt-2 pt-2 border-t border-border">
                      <button
                        type="button"
                        suppressHydrationWarning
                        onClick={() =>
                          setExpandedId(isExpanded ? null : evt.id)
                        }
                        className="flex items-center gap-1 text-[10px] font-mono text-fg-subtle hover:text-fg transition-colors"
                      >
                        <span>
                          {isExpanded ? "Hide Safe Metadata" : "View Safe Metadata"}
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="h-3 w-3" />
                        ) : (
                          <ChevronDown className="h-3 w-3" />
                        )}
                      </button>

                      {isExpanded && (
                        <pre className="mt-2 rounded-lg bg-surface p-2.5 font-mono text-[10px] text-fg-muted border border-border overflow-x-auto leading-relaxed">
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
