import React from "react";
import Link from "next/link";
import { ArrowLeft, Home, Shield } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-canvas text-fg flex flex-col items-center justify-center p-6 space-y-6 font-sans">
      <div className="h-12 w-12 rounded-2xl bg-canvas-subtle border border-border flex items-center justify-center text-accent">
        <Shield className="h-6 w-6" />
      </div>

      <div className="text-center space-y-2 max-w-sm">
        <span className="font-mono text-xs text-accent font-bold uppercase tracking-wider">
          404 · Page Not Found
        </span>
        <h1 className="text-2xl font-bold tracking-tight text-fg">
          Destination does not exist
        </h1>
        <p className="text-xs text-fg-muted leading-relaxed">
          The requested path could not be found. Use the primary navigation to return to the active Trade Desk or portfolio.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/app"
          className="rounded-xl bg-accent px-5 py-2.5 text-xs font-semibold text-white shadow-subtle hover:bg-accent-dark transition-all flex items-center gap-2"
        >
          <Home className="h-3.5 w-3.5" />
          <span>Go to Trade Desk</span>
        </Link>
        <Link
          href="/"
          className="rounded-xl border border-border bg-surface px-5 py-2.5 text-xs font-semibold text-fg hover:bg-surface-hover transition-all flex items-center gap-2 shadow-subtle"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Home</span>
        </Link>
      </div>
    </div>
  );
}
