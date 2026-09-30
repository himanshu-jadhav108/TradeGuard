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

  const getEventIcon = (type: string) => {
    switch (type) {
      case "ORDER_FILLED":
      case "TRADE_CONFIRMED":
        return <CheckCircle2 className="h-4 w-4 text-emerald" />;
      case "PROPOSAL_CREATED":
        return <FileText className="h-4 w-4 text-warn" />;
      case "ACCOUNT_SEEDED":
        return <ShieldCheck className="h-4 w-4 text-emerald" />;
      default:
        return <Clock className="h-4 w-4 text-fg-subtle" />;
    }
  };

  return (
    <div className="w-full rounded-2xl border border-border bg-surface p-6 shadow-card">
      <div className="flex items-center justify-between mb-6 pb-3 border-b border-border">
        <div>
          <h3 className="text-sm font-semibold text-fg">
            Immutable Audit Trail & Execution Timeline
          </h3>
          <p className="text-xs text-fg-subtle mt-0.5">
            Cryptographic and deterministic event stream logged prior to execution
          </p>
        </div>
        <button
          onClick={fetchActivity}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1 text-xs text-fg-muted hover:text-fg hover:bg-surface-hover transition-colors"
        >
          <RefreshCw
            className={`h-3 w-3 ${loading ? "animate-spin text-emerald" : ""}`}
          />
          <span>Refresh</span>
        </button>
      </div>

      {loading && events.length === 0 ? (
        <div className="py-8 text-center text-xs text-fg-subtle">
          <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-emerald" />
          <span>Loading activity stream...</span>
        </div>
      ) : events.length === 0 ? (
        <div className="py-8 text-center text-xs text-fg-subtle">
          No audit events recorded yet.
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
          {events.map((evt) => {
            const isExpanded = expandedId === evt.id;
            return (
              <div key={evt.id} className="relative group">
                {/* Timeline node */}
                <div className="absolute -left-6 top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-surface border border-border shadow-sm group-hover:border-emerald transition-colors">
                  {getEventIcon(evt.event_type)}
                </div>

                <div className="rounded-xl border border-border bg-canvas-subtle p-3.5 transition-all hover:border-emerald/40">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-surface px-2 py-0.5 font-mono text-[10px] font-bold text-fg border border-border">
                        {evt.event_type}
                      </span>
                      {evt.proposal_id && (
                        <span className="font-mono text-[10px] text-fg-subtle">
                          {evt.proposal_id}
                        </span>
                      )}
                      {evt.order_id && (
                        <span className="font-mono text-[10px] text-emerald font-semibold">
                          {evt.order_id}
                        </span>
                      )}
                    </div>
                    <span className="font-mono text-[11px] text-fg-subtle">
                      {new Date(evt.timestamp).toLocaleTimeString()} ·{" "}
                      {new Date(evt.timestamp).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="mt-2 text-xs font-medium text-fg">
                    {evt.summary}
                  </p>

                  {/* Metadata Toggle */}
                  {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-border">
                      <button
                        onClick={() =>
                          setExpandedId(isExpanded ? null : evt.id)
                        }
                        className="flex items-center gap-1 text-[11px] font-mono text-fg-subtle hover:text-fg transition-colors"
                      >
                        <span>
                          {isExpanded ? "Hide Metadata" : "View Safe Metadata"}
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="h-3 w-3" />
                        ) : (
                          <ChevronDown className="h-3 w-3" />
                        )}
                      </button>

                      {isExpanded && (
                        <pre className="mt-2 rounded-lg bg-surface p-2.5 font-mono text-[11px] text-fg-muted border border-border overflow-x-auto">
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
