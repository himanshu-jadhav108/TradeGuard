import React from "react";

export default function Loading() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="min-h-screen bg-canvas text-fg flex flex-col items-center justify-center p-6 space-y-4 font-sans"
    >
      <div className="relative flex items-center justify-center">
        <div className="h-10 w-10 rounded-full border-2 border-border border-t-accent animate-spin" />
        <span className="sr-only">Loading TradeGuard...</span>
      </div>
      <div className="text-center space-y-1">
        <p className="text-sm font-semibold text-fg tracking-tight">Connecting to TradeGuard…</p>
        <p className="text-xs text-fg-subtle font-mono">Initializing pre-trade verification layer</p>
      </div>
    </div>
  );
}
