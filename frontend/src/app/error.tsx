"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log non-sensitive client error to console
    console.error("TradeGuard application error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-canvas text-fg flex flex-col items-center justify-center p-6 space-y-6 font-sans">
      <div className="h-12 w-12 rounded-2xl bg-danger/10 border border-danger/20 flex items-center justify-center text-danger">
        <AlertTriangle className="h-6 w-6" />
      </div>

      <div className="text-center space-y-2 max-w-md">
        <h1 className="text-xl font-bold tracking-tight text-fg">
          Something went wrong
        </h1>
        <p className="text-xs text-fg-muted leading-relaxed">
          TradeGuard encountered an unexpected error while processing this view. No trades or balances were affected.
        </p>
        {error.message && (
          <div className="p-3 rounded-xl bg-canvas-subtle border border-border text-left font-mono text-[11px] text-danger max-h-24 overflow-y-auto">
            {error.message}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={() => reset()}
          className="rounded-xl bg-accent px-5 py-2.5 text-xs font-semibold text-white shadow-subtle hover:bg-accent-dark transition-all flex items-center gap-2"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Try again</span>
        </button>
        <Link
          href="/app"
          className="rounded-xl border border-border bg-surface px-5 py-2.5 text-xs font-semibold text-fg hover:bg-surface-hover transition-all flex items-center gap-2 shadow-subtle"
        >
          <Home className="h-3.5 w-3.5" />
          <span>Return to Trade Desk</span>
        </Link>
      </div>
    </div>
  );
}
