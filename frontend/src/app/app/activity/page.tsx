"use client";

import React from "react";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { useRefresh } from "@/lib/refresh-context";
import Link from "next/link";
import { ArrowLeft, ShieldCheck } from "lucide-react";

export default function ActivityPage() {
  const { refreshKey } = useRefresh();
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/app"
              className="text-xs text-fg-subtle hover:text-fg transition-colors flex items-center gap-1 font-mono"
            >
              <ArrowLeft className="h-3 w-3" />
              <span>Trade Desk</span>
            </Link>
            <span className="text-fg-subtle text-xs">/</span>
            <span className="text-xs font-mono text-accent">Activity</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
            Activity & Audit Log
          </h1>
          <p className="text-xs text-fg-subtle mt-0.5">
            Chronological session records for intent interpretations, deterministic risk evaluations, and trade confirmations
          </p>
        </div>

        <div className="flex items-center gap-1.5 rounded-full border border-border bg-canvas-subtle px-3 py-1 text-xs">
          <ShieldCheck className="h-3.5 w-3.5 text-accent" />
          <span className="font-mono text-[11px] font-medium text-fg-muted">
            Session Activity Log
          </span>
        </div>
      </div>

      <ActivityTimeline refreshTrigger={refreshKey} />
    </div>
  );
}
