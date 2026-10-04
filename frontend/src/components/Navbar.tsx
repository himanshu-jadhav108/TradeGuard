"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useTheme } from "@/lib/theme";
import { Sun, Moon, RefreshCw, CheckCircle2, Menu, X, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";

export function Navbar({ onReset }: { onReset?: () => void }) {
  const { theme, toggleTheme } = useTheme();
  const pathname = usePathname();
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const isApp = pathname?.startsWith("/app");

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

  const appNavLinks = [
    { href: "/app", label: "Trade Desk" },
    { href: "/app/portfolio", label: "Portfolio" },
    { href: "/app/activity", label: "Activity" },
  ];

  const landingNavLinks = [
    { id: "preview", href: "#preview", label: "Preview" },
    { id: "flow", href: "#flow", label: "Workflow" },
    { id: "philosophy", href: "#philosophy", label: "Philosophy" },
    { id: "true-markets", href: "#true-markets", label: "Integration" },
  ];

  const [activeSection, setActiveSection] = useState<string>("");

  React.useEffect(() => {
    if (isApp) return;

    const sectionIds = ["preview", "flow", "philosophy", "true-markets"];
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 160;
      let current = "";
      for (const id of sectionIds) {
        const element = document.getElementById(id);
        if (element) {
          const top = element.offsetTop;
          if (scrollPosition >= top) {
            current = id;
          }
        }
      }
      setActiveSection(current);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });

    // Initial check
    if (typeof window !== "undefined" && window.location.hash) {
      const hashId = window.location.hash.replace("#", "");
      if (sectionIds.includes(hashId)) {
        setActiveSection(hashId);
      }
    } else {
      handleScroll();
    }

    return () => window.removeEventListener("scroll", handleScroll);
  }, [isApp]);

  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
      window.history.pushState(null, "", `#${id}`);
      setActiveSection(id);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface/95 backdrop-blur-md transition-colors shadow-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo & Wordmark */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-surface border border-border group-hover:border-accent/60 transition-colors shadow-subtle">
            <Image
              src="/branding/tradeguard-logo.png"
              alt="TradeGuard"
              width={22}
              height={22}
              className="drop-shadow-sm rounded-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-base font-semibold tracking-tight text-fg">
              TradeGuard
            </span>
            <span className="rounded px-1.5 py-0.5 font-mono text-[10px] font-semibold bg-accent-surface text-accent border border-accent/20">
              DEMO · SIMULATED
            </span>
          </div>
        </Link>

        {/* Center Desktop Navigation */}
        {isApp ? (
          <nav className="hidden md:flex items-center gap-1 rounded-lg border border-border bg-canvas-subtle p-1">
            {appNavLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
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
        ) : (
          <nav className="hidden md:flex items-center gap-1 rounded-lg border border-border bg-canvas-subtle p-1">
            {landingNavLinks.map((link) => {
              const active = activeSection === link.id;
              return (
                <a
                  key={link.id}
                  href={link.href}
                  onClick={(e) => scrollToSection(e, link.id)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                    active
                      ? "bg-surface text-accent font-semibold shadow-subtle border border-border"
                      : "text-fg-muted hover:text-fg hover:bg-surface-hover"
                  }`}
                >
                  {link.label}
                </a>
              );
            })}
          </nav>
        )}

        {/* Right Desktop Actions */}
        <div className="hidden sm:flex items-center gap-2.5">
          {/* Simulated Mode Pill */}
          <div className="flex items-center gap-1.5 rounded-full border border-border bg-canvas-subtle px-2.5 py-1 text-xs">
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
            <span className="font-mono text-[11px] font-medium text-fg-muted">
              DEMO
            </span>
          </div>

          {/* Reset / Restart Demo Button */}
          <button
            type="button"
            suppressHydrationWarning
            onClick={handleReset}
            disabled={resetting}
            title="Reset demo account to initial state"
            className="flex items-center gap-1 rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs font-medium text-fg-muted hover:text-fg hover:bg-surface-hover transition-colors shadow-subtle"
          >
            <RefreshCw
              className={`h-3 w-3 ${resetting ? "animate-spin text-accent" : ""}`}
            />
            <span className="text-xs">
              {resetSuccess ? "Reset!" : "Reset Demo"}
            </span>
            {resetSuccess && (
              <CheckCircle2 className="h-3 w-3 text-accent" />
            )}
          </button>

          {/* Theme Toggle Button */}
          <button
            type="button"
            suppressHydrationWarning
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface text-fg-muted hover:text-fg hover:bg-surface-hover transition-colors shadow-subtle"
          >
            {mounted ? (
              theme === "dark" ? (
                <Sun className="h-3.5 w-3.5 text-warn" />
              ) : (
                <Moon className="h-3.5 w-3.5 text-fg" />
              )
            ) : (
              <span className="h-3.5 w-3.5" />
            )}
          </button>

          {/* Launch App / Home Link */}
          {!isApp ? (
            <Link
              href="/app"
              className="rounded-lg bg-accent px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-accent-dark transition-all shadow-subtle flex items-center gap-1.5"
            >
              <span>Launch App</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          ) : (
            <Link
              href="/"
              className="text-xs font-medium text-fg-subtle hover:text-fg transition-colors px-2 py-1"
            >
              Home
            </Link>
          )}
        </div>

        {/* Mobile Menu Button */}
        <div className="flex sm:hidden items-center gap-2">
          <button
            type="button"
            suppressHydrationWarning
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface text-fg-muted"
          >
            {mounted ? (
              theme === "dark" ? (
                <Sun className="h-3.5 w-3.5 text-warn" />
              ) : (
                <Moon className="h-3.5 w-3.5 text-fg" />
              )
            ) : (
              <span className="h-3.5 w-3.5" />
            )}
          </button>
          <button
            type="button"
            suppressHydrationWarning
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface text-fg"
          >
            {mobileMenuOpen ? (
              <X className="h-4 w-4" />
            ) : (
              <Menu className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="sm:hidden border-t border-border bg-surface px-4 py-4 space-y-3">
          <nav className="flex flex-col space-y-1">
            {isApp
              ? appNavLinks.map((link) => {
                  const active = pathname === link.href;
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`px-3 py-2 text-xs font-medium rounded-lg ${
                        active
                          ? "bg-canvas-subtle text-fg font-semibold"
                          : "text-fg-muted hover:text-fg"
                      }`}
                    >
                      {link.label}
                    </Link>
                  );
                })
              : landingNavLinks.map((link) => {
                  const active = activeSection === link.id;
                  return (
                    <a
                      key={link.id}
                      href={link.href}
                      onClick={(e) => scrollToSection(e, link.id)}
                      className={`px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                        active
                          ? "bg-canvas-subtle text-accent font-semibold border border-border"
                          : "text-fg-muted hover:text-fg"
                      }`}
                    >
                      {link.label}
                    </a>
                  );
                })}
          </nav>

          <div className="pt-3 border-t border-border flex flex-col gap-2">
            <button
              type="button"
              suppressHydrationWarning
              onClick={() => {
                handleReset();
                setMobileMenuOpen(false);
              }}
              disabled={resetting}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-border bg-canvas-subtle py-2 text-xs font-medium text-fg"
            >
              <RefreshCw
                className={`h-3 w-3 ${resetting ? "animate-spin text-accent" : ""}`}
              />
              <span>{resetSuccess ? "Demo Account Reset!" : "Reset Demo Account"}</span>
            </button>

            {isApp ? (
              <Link
                href="/"
                onClick={() => setMobileMenuOpen(false)}
                className="text-center text-xs text-fg-subtle hover:text-fg py-1"
              >
                Back to Landing Page
              </Link>
            ) : (
              <Link
                href="/app"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center justify-center gap-1.5 rounded-lg bg-accent py-2.5 text-xs font-semibold text-white"
              >
                <span>Launch App</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
