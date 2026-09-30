"use client";

import React from "react";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { useRefresh } from "@/lib/refresh-context";

export default function ActivityPage() {
  const { refreshKey } = useRefresh();
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
          Audit Activity & Execution Log
        </h1>
        <p className="text-xs text-fg-subtle mt-1">
          Chronological cryptographic audit stream for intent parsing, risk checks, and trade settlements
        </p>
      </div>

      <ActivityTimeline refreshTrigger={refreshKey} />
    </div>
  );
}
