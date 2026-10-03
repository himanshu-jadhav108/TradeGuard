"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useTheme } from "@/lib/theme";
import { Sun, Moon, Shield, RefreshCw, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export function Navbar({ onReset }: { onReset?: () => void }) {
  const { theme, toggleTheme } = useTheme();
  const pathname = usePathname();
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  const handleReset = async () => {
    try {
      setResetting(true);
      await api.resetDemo();
      setResetSuccess(true);
      if (onReset) onReset();
      setTimeout(() => setResetSuccess(false), 2000);
    } catch (e) {
      console.error("Reset error:", e);
    } finally {
      setResetting(false);
    }
  };

  const navLinks = [
    { href: "/app", label: "Overview" },
    { href: "/app/trade", label: "Trade" },
    { href: "/app/portfolio", label: "Portfolio" },
    { href: "/app/activity", label: "Activity" },
  ];

  const isApp = pathname?.startsWith("/app");

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface/90 backdrop-blur-md transition-colors">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo & Tagline */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-canvas-subtle border border-border group-hover:border-emerald transition-colors">
            <Image
              src="/branding/tradeguard-logo.svg"
              alt="TradeGuard"
              width={26}
              height={26}
              className="drop-shadow"
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg tracking-tight">
                <span className="font-bold text-fg">Trade</span>
                <span className="font-bold bg-gradient-to-r from-emerald-light via-emerald to-cyan-400 bg-clip-text text-transparent">Guard</span>
              </span>
              <span className="rounded-full bg-emerald-surface px-2 py-0.5 text-[10px] font-medium text-emerald border border-emerald/20">
                v1.0
              </span>
            </div>
            <p className="text-[11px] text-fg-subtle hidden sm:block">
              Think before you trade.
            </p>
          </div>
        </Link>

        {/* Center Navigation if in App */}
        {isApp && (
          <nav className="hidden md:flex items-center gap-1 rounded-lg border border-border bg-canvas-subtle p-1">
            {navLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    active
                      ? "bg-surface text-fg shadow-subtle border border-border"
                      : "text-fg-muted hover:text-fg hover:bg-surface-hover"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        )}

        {/* Right Actions: Mode Badge, Reset Demo, Theme Toggle, CTA */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Mode Pill */}
          <div className="flex items-center gap-1.5 rounded-full border border-border bg-canvas-subtle px-2.5 py-1 text-xs">
            <span className="h-2 w-2 rounded-full bg-emerald animate-pulse" />
            <span className="font-mono text-[11px] font-medium text-fg-muted">
              DEMO MODE
            </span>
          </div>

          {/* Reset Demo Button */}
          {isApp && (
            <button
              onClick={handleReset}
              disabled={resetting}
              title="Reset demo account to initial state"
              className="flex items-center gap-1 rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs font-medium text-fg-muted hover:text-fg hover:bg-surface-hover transition-colors"
            >
              <RefreshCw
                className={`h-3.5 w-3.5 ${resetting ? "animate-spin text-emerald" : ""}`}
              />
              <span className="hidden sm:inline">
                {resetSuccess ? "Reset!" : "Reset Demo"}
              </span>
              {resetSuccess && (
                <CheckCircle2 className="h-3 w-3 text-emerald" />
              )}
            </button>
          )}

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            aria-label="Toggle color theme"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-fg-muted hover:text-fg hover:bg-surface-hover transition-colors"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 text-warn" />
            ) : (
              <Moon className="h-4 w-4 text-fg" />
            )}
          </button>

          {/* App / Landing Link Button */}
          {!isApp ? (
            <Link
              href="/app"
              className="rounded-lg bg-emerald px-4 py-2 text-xs font-medium text-white hover:bg-emerald-dark transition-colors shadow-sm"
            >
              Launch App
            </Link>
          ) : (
            <Link
              href="/"
              className="text-xs text-fg-subtle hover:text-fg transition-colors hidden sm:block"
            >
              Home
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
