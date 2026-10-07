"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { AuditEvent } from "@/lib/types";
import { api } from "@/lib/api";
import {
  CheckCircle2,
  AlertTriangle,
  FileText,
  ShieldCheck,
  Clock,
  ArrowRight,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

interface RecentActivityPreviewProps {
  refreshTrigger?: number;
}

export function RecentActivityPreview({ refreshTrigger }: RecentActivityPreviewProps) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecent = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getActivity(5);
      setEvents(data.slice(0, 5));
    } catch (err: any) {
      console.error("Recent activity preview fetch error:", err);
      setError(err.message || "Failed to load recent activity");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecent();
  }, [refreshTrigger]);

  const getEventBadge = (type: string) => {
    switch (type) {
      case "ORDER_FILLED":
      case "TRADE_CONFIRMED":
        return {
          icon: <CheckCircle2 className="h-3.5 w-3.5 text-accent" />,
          label: "Confirmed",
          style: "bg-accent-surface text-accent border-accent/20",
        };
      case "WARNING_ACKNOWLEDGED":
        return {
          icon: <CheckCircle2 className="h-3.5 w-3.5 text-accent" />,
          label: "Warn Ack",
          style: "bg-accent-surface text-accent border-accent/20",
        };
      case "RISK_EVALUATED":
      case "PROPOSAL_CREATED":
        return {
          icon: <ShieldCheck className="h-3.5 w-3.5 text-accent" />,
          label: "Risk Check",
          style: "bg-accent-surface text-accent border-accent/20",
        };
      case "CONFIRM_REJECTED":
      case "ORDER_FAILED":
        return {
          icon: <AlertCircle className="h-3.5 w-3.5 text-danger" />,
          label: "Rejected",
          style: "bg-danger-surface text-danger border-danger/20",
        };
      case "INTENT_PARSED":
        return {
          icon: <FileText className="h-3.5 w-3.5 text-accent" />,
          label: "Parsed",
          style: "bg-accent-surface text-accent border-accent/20",
        };
      case "INTENT_REJECTED":
        return {
          icon: <AlertCircle className="h-3.5 w-3.5 text-warn" />,
          label: "Rejected",
          style: "bg-warn-surface text-warn border-warn/20",
        };
      case "PROPOSAL_EXPIRED":
        return {
          icon: <Clock className="h-3.5 w-3.5 text-warn" />,
          label: "Expired",
          style: "bg-warn-surface text-warn border-warn/20",
        };
      case "TRADE_CANCELLED":
        return {
          icon: <Clock className="h-3.5 w-3.5 text-fg-subtle" />,
          label: "Cancelled",
          style: "bg-canvas-subtle text-fg-subtle border-border",
        };
      case "ACCOUNT_SEEDED":
      case "ACCOUNT_RESET":
        return {
          icon: <ShieldCheck className="h-3.5 w-3.5 text-fg-muted" />,
          label: "System",
          style: "bg-canvas-subtle text-fg-muted border-border",
        };
      default:
        return {
          icon: <Clock className="h-3.5 w-3.5 text-fg-subtle" />,
          label: "Event",
          style: "bg-canvas-subtle text-fg-subtle border-border",
        };
    }
  };

  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-subtle precision-rail">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-fg-muted">
            Recent Activity
          </span>
          <span className="text-[10px] font-mono text-fg-subtle px-1.5 py-0.2 rounded bg-canvas-subtle border border-border">
            Audit Stream
          </span>
        </div>
        <Link
          href="/app/activity"
          className="text-xs font-semibold text-accent hover:text-accent-dark transition-colors flex items-center gap-1 group"
        >
          <span>View all</span>
          <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>

      {/* Content */}
      {loading && events.length === 0 ? (
        <div className="py-6 text-center text-xs text-fg-subtle flex items-center justify-center gap-2">
          <RefreshCw className="h-3.5 w-3.5 animate-spin text-accent" />
          <span>Loading activity...</span>
        </div>
      ) : error && events.length === 0 ? (
        <div className="py-4 text-center text-xs text-danger flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>Could not load recent events</span>
          </div>
          <button
            type="button"
            onClick={fetchRecent}
            className="text-xs font-semibold text-accent hover:underline flex items-center gap-1"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Retry</span>
          </button>
        </div>
      ) : events.length === 0 ? (
        <div className="py-6 text-center text-xs text-fg-subtle">
          No recent activity recorded. Submit a trade intent above to initiate the pre-trade review lifecycle.
        </div>
      ) : (
        <div className="space-y-2">
          {events.map((evt) => {
            const badge = getEventBadge(evt.event_type);
            const prompt = evt.metadata?.raw_prompt;

            return (
              <div
                key={evt.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 p-2 rounded-lg bg-canvas-subtle border border-border/70 text-xs transition-colors hover:border-accent/40"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-bold border flex items-center gap-1 shrink-0 ${badge.style}`}
                  >
                    {badge.icon}
                    <span>{badge.label}</span>
                  </span>
                  <span className="font-medium text-fg truncate text-xs">
                    {prompt ? `“${prompt}”` : evt.summary}
                  </span>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto font-mono text-[11px] text-fg-subtle">
                  {evt.proposal_id && (
                    <span className="text-[10px] hidden md:inline text-fg-muted">
                      {evt.proposal_id}
                    </span>
                  )}
                  <time>{new Date(evt.timestamp).toLocaleTimeString()}</time>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
