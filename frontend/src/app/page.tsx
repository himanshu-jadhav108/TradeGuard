"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Navbar } from "@/components/Navbar";
import { TradeComposer } from "@/components/TradeComposer";
import { TradeReviewCard } from "@/components/TradeReviewCard";
import { DemoVideoSection } from "@/components/DemoVideoSection";
import { TradeProposal, OrderRecord } from "@/lib/types";
import {
  ShieldCheck,
  Lock,
  ArrowRight,
  Cpu,
  CheckCircle,
  FileCheck2,
  Terminal,
  Activity,
  Layers,
  ChevronRight,
  ExternalLink,
} from "lucide-react";

export default function LandingPage() {
  const [activeProposal, setActiveProposal] = useState<TradeProposal | null>(
    null
  );

  return (
    <div className="min-h-screen bg-canvas text-fg selection:bg-emerald/20 selection:text-emerald">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-24 sm:py-20">
        {/* SECTION 1: HERO */}
        <section className="text-center space-y-6 max-w-4xl mx-auto pt-4 sm:pt-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-1 text-xs font-medium text-fg-muted shadow-subtle">
            <span className="h-2 w-2 rounded-full bg-emerald" />
            <span>Built for True Markets “Build the Next Wealth App” Challenge</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-fg leading-[1.08]">
            Think before <br />
            <span className="text-emerald">you trade.</span>
          </h1>

          <p className="text-base sm:text-xl text-fg-muted max-w-2xl mx-auto font-normal leading-relaxed">
            AI-assisted execution with live market context, deterministic risk checks, and strict human control before any money moves.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              href="/app"
              className="rounded-xl bg-emerald px-6 py-3.5 text-sm font-semibold text-white shadow-md hover:bg-emerald-dark transition-all flex items-center gap-2 group"
            >
              <span>Try TradeGuard</span>
              <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <a
              href="#demo-walkthrough"
              className="rounded-xl border border-border bg-surface px-6 py-3.5 text-sm font-semibold text-fg hover:bg-surface-hover transition-all"
            >
              Watch 2-Min Demo
            </a>
          </div>
        </section>

        {/* SECTION 2: INTERACTIVE PRODUCT PREVIEW */}
        <section className="space-y-6">
          <div className="text-center space-y-1">
            <span className="text-[11px] font-mono uppercase tracking-wider text-emerald font-semibold">
              Live Interactive Preview
            </span>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-fg">
              Experience the Trade Review Flow
            </h2>
            <p className="text-xs text-fg-subtle max-w-lg mx-auto">
              Enter a prompt or select a 1-click test below. Watch the deterministic risk engine evaluate your order in real time.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-5 space-y-4">
              <TradeComposer
                onProposalCreated={(prop) => setActiveProposal(prop)}
              />
              <div className="rounded-xl border border-border bg-canvas-subtle p-4 text-xs text-fg-subtle space-y-2">
                <span className="font-semibold text-fg block text-[11px]">
                  What happens when you enter an intent?
                </span>
                <p>
                  1. Structured intent extraction ({`{ asset, side, amount }`})<br />
                  2. Live quote snapshot retrieved (spread & TTL calculated)<br />
                  3. 5-point deterministic risk check runs server-side<br />
                  4. Explainable summary generated prior to any confirmation
                </p>
              </div>
            </div>

            <div className="lg:col-span-7">
              {activeProposal ? (
                <TradeReviewCard
                  proposal={activeProposal}
                  onTradeConfirmed={(order) => {}}
                  onCancelled={() => setActiveProposal(null)}
                />
              ) : (
                <div className="rounded-2xl border border-dashed border-border bg-surface/50 p-12 text-center text-fg-subtle flex flex-col items-center justify-center min-h-[360px]">
                  <div className="h-12 w-12 rounded-xl bg-canvas-subtle border border-border flex items-center justify-center mb-3 text-fg-muted">
                    <FileCheck2 className="h-6 w-6 text-emerald" />
                  </div>
                  <h3 className="text-sm font-semibold text-fg">
                    Awaiting Trade Intent
                  </h3>
                  <p className="text-xs text-fg-subtle max-w-sm mt-1">
                    Select <span className="font-mono text-fg">“Buy $500 of BTC”</span> on the left to see the signature Trade Review card.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* SECTION 3: FOUR-STEP WORKFLOW */}
        <section className="space-y-10 py-6 border-t border-border">
          <div className="text-center space-y-2 max-w-xl mx-auto">
            <span className="text-[11px] font-mono uppercase tracking-wider text-emerald font-semibold">
              The Architecture of Control
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
              Four steps from intent to settlement.
            </h2>
            <p className="text-xs sm:text-sm text-fg-muted">
              Designed around an unbreakable boundary: AI suggests, deterministic rules govern, human confirms.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Step 1 */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-canvas-subtle font-mono text-sm font-bold text-fg border border-border">
                01
              </div>
              <h3 className="text-base font-semibold text-fg">Understand</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Natural-language trade requests are converted into strict, typed domain intents. Malformed requests are rejected safely.
              </p>
            </div>

            {/* Step 2 */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-canvas-subtle font-mono text-sm font-bold text-fg border border-border">
                02
              </div>
              <h3 className="text-base font-semibold text-fg">Check</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                The deterministic backend risk engine evaluates asset allowlists, cash balances, maximum notional ceilings, and concentration warnings.
              </p>
            </div>

            {/* Step 3 */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-surface font-mono text-sm font-bold text-emerald border border-emerald/20">
                03
              </div>
              <h3 className="text-base font-semibold text-fg">Confirm</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                The user reviews the live quote, fill estimate, and exposure impact. Nothing moves without explicit human authorization.
              </p>
            </div>

            {/* Step 4 */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-canvas-subtle font-mono text-sm font-bold text-fg border border-border">
                04
              </div>
              <h3 className="text-base font-semibold text-fg">Execute</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Dispatches order to True Markets Gateway via isolated server-side adapter. Logs an immutable audit event and updates portfolio state.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 4: SECURITY & CONTROL GUARANTEES */}
        <section className="rounded-3xl border border-border bg-surface p-8 sm:p-12 shadow-card space-y-8">
          <div className="max-w-2xl space-y-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-emerald font-semibold">
              Security Specifications
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
              Fintech-grade trust guarantees.
            </h2>
            <p className="text-xs sm:text-sm text-fg-muted">
              Built with Apple-level restraint and strict zero-trust boundaries between language models and financial execution.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-xl border border-border bg-canvas-subtle p-5 space-y-2.5">
              <div className="flex items-center gap-2 text-fg font-semibold text-sm">
                <Lock className="h-4 w-4 text-emerald" />
                <span>Zero Autonomous Execution</span>
              </div>
              <p className="text-xs text-fg-muted leading-relaxed">
                The model cannot trigger trade settlement. Every order requires explicit cryptographic authorization from the user.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-canvas-subtle p-5 space-y-2.5">
              <div className="flex items-center gap-2 text-fg font-semibold text-sm">
                <ShieldCheck className="h-4 w-4 text-emerald" />
                <span>Deterministic Risk Overrides</span>
              </div>
              <p className="text-xs text-fg-muted leading-relaxed">
                Authoritative numbers and balance checks are owned exclusively by Python backend code. A <span className="font-mono text-danger font-bold">BLOCK</span> status cannot be bypassed by prompts.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-canvas-subtle p-5 space-y-2.5">
              <div className="flex items-center gap-2 text-fg font-semibold text-sm">
                <Cpu className="h-4 w-4 text-emerald" />
                <span>Backend Credential Isolation</span>
              </div>
              <p className="text-xs text-fg-muted leading-relaxed">
                True Markets API keys and signer private keys never touch the browser or git repository.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 5: DEMO VIDEO SECTION */}
        <section id="demo-walkthrough" className="space-y-6 pt-6">
          <DemoVideoSection />
        </section>

        {/* SECTION 6: TRUE MARKETS INTEGRATION BADGE */}
        <section className="rounded-2xl border border-border bg-canvas-subtle p-6 text-center space-y-3">
          <div className="flex items-center justify-center gap-2 text-xs font-mono text-fg-muted">
            <span className="h-2 w-2 rounded-full bg-emerald" />
            <span>True Markets Retail Gateway Architecture</span>
          </div>
          <p className="text-xs text-fg-subtle max-w-xl mx-auto">
            TradeGuard connects to the True Markets UAT Gateway (<span className="font-mono">https://api.uat.truemarkets.co/v1/gateway</span>) for quoting, order creation, transaction signing, and settlement status polling.
          </p>
        </section>

        {/* SECTION 7: FINAL CTA */}
        <section className="text-center space-y-4 py-8">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
            Ready to experience TradeGuard?
          </h2>
          <p className="text-xs sm:text-sm text-fg-muted max-w-md mx-auto">
            Explore the simulated demo portfolio or configure UAT Gateway credentials.
          </p>
          <div className="pt-2">
            <Link
              href="/app"
              className="inline-flex items-center gap-2 rounded-xl bg-emerald px-6 py-3.5 text-sm font-semibold text-white shadow-md hover:bg-emerald-dark transition-all"
            >
              <span>Launch Application</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>

      {/* MINIMAL FOOTER */}
      <footer className="border-t border-border bg-surface py-8 text-center text-xs text-fg-subtle transition-colors">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Image
              src="/branding/tradeguard-logo.svg"
              alt="TradeGuard"
              width={18}
              height={18}
            />
            <span className="font-bold">
              <span className="text-fg">Trade</span>
              <span className="bg-gradient-to-r from-emerald-light via-emerald to-cyan-400 bg-clip-text text-transparent">Guard</span>
            </span>
            <span>— Think before you trade.</span>
          </div>
          <div className="flex items-center gap-4 text-fg-subtle text-[11px]">
            <span>True Markets Hackathon Edition</span>
            <span>•</span>
            <Link href="/app" className="hover:text-fg transition-colors">
              App
            </Link>
            <span>•</span>
            <Link href="/app/portfolio" className="hover:text-fg transition-colors">
              Portfolio
            </Link>
            <span>•</span>
            <Link href="/app/activity" className="hover:text-fg transition-colors">
              Audit
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
