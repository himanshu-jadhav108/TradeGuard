"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Navbar } from "@/components/Navbar";
import { TradeComposer } from "@/components/TradeComposer";
import { TradeReviewCard } from "@/components/TradeReviewCard";
import { TradeProposal, OrderRecord } from "@/lib/types";
import {
  ShieldCheck,
  Lock,
  ArrowRight,
  Cpu,
  FileCheck2,
  Terminal,
  Activity,
  Layers,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  PieChart,
  ShieldAlert,
  Server,
  KeyRound,
  FileText,
} from "lucide-react";

export default function LandingPage() {
  const [activeProposal, setActiveProposal] = useState<TradeProposal | null>(
    null
  );

  return (
    <div className="min-h-screen bg-canvas text-fg selection:bg-accent/20 selection:text-accent font-sans">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-24 sm:space-y-32 sm:py-16">
        {/* ========================================================================= */}
        {/* 1. HERO SECTION                                                          */}
        {/* ========================================================================= */}
        <section className="text-center space-y-6 max-w-4xl mx-auto pt-4 sm:pt-8">
          {/* Institutional Trust Eyebrow */}
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-1 text-xs font-medium text-fg-muted shadow-subtle">
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
            <span>Institutional Pre-Trade Execution Layer · True Markets Native</span>
          </div>

          {/* Core Brand & Tagline */}
          <div className="space-y-3">
            <span className="font-mono text-xs uppercase tracking-widest text-fg-subtle font-semibold block">
              TradeGuard
            </span>
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-fg leading-[1.08]">
              Think before <br />
              <span className="text-accent">you trade.</span>
            </h1>
          </div>

          {/* Exact Core Message */}
          <p className="text-base sm:text-xl text-fg-muted max-w-2xl mx-auto font-normal leading-relaxed">
            Turn natural-language trade intent into a transparent, risk-checked and human-confirmed trade.
          </p>

          {/* Primary & Secondary Action Triggers */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              href="/app"
              className="rounded-xl bg-accent px-6 py-3.5 text-sm font-semibold text-white shadow-subtle hover:bg-accent-dark transition-all flex items-center gap-2 group"
            >
              <span>Try TradeGuard</span>
              <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <a
              href="#how-it-works"
              className="rounded-xl border border-border bg-surface px-6 py-3.5 text-sm font-semibold text-fg hover:bg-surface-hover transition-all shadow-subtle"
            >
              See how it works
            </a>
          </div>

          {/* System Operational Indicators */}
          <div className="pt-6 grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl mx-auto text-left">
            <div className="rounded-xl border border-border bg-surface p-3 text-xs flex items-center gap-2.5">
              <ShieldCheck className="h-4 w-4 text-accent shrink-0" />
              <div>
                <span className="font-semibold text-fg block text-[11px]">Deterministic Risk</span>
                <span className="text-fg-subtle text-[10px]">Server-side limits & balance check</span>
              </div>
            </div>
            <div className="rounded-xl border border-border bg-surface p-3 text-xs flex items-center gap-2.5">
              <Clock className="h-4 w-4 text-accent shrink-0" />
              <div>
                <span className="font-semibold text-fg block text-[11px]">Live Market Quotes</span>
                <span className="text-fg-subtle text-[10px]">30s TTL freshness window</span>
              </div>
            </div>
            <div className="rounded-xl border border-border bg-surface p-3 text-xs flex items-center gap-2.5">
              <Lock className="h-4 w-4 text-accent shrink-0" />
              <div>
                <span className="font-semibold text-fg block text-[11px]">Human Confirmation</span>
                <span className="text-fg-subtle text-[10px]">Zero autonomous execution</span>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 2. INTERACTIVE PRODUCT PREVIEW                                           */}
        {/* ========================================================================= */}
        <section id="preview" className="space-y-8 scroll-mt-24">
          <div className="text-center space-y-1.5 max-w-xl mx-auto">
            <span className="text-[11px] font-mono uppercase tracking-wider text-accent font-semibold">
              Interactive Product Preview
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
              The Trade Review Lifecycle
            </h2>
            <p className="text-xs sm:text-sm text-fg-subtle">
              Experience how natural language trade intent is validated and converted into a deterministic order proposal.
            </p>
          </div>

          {/* Workflow Stepper Ribbon */}
          <div className="rounded-2xl border border-border bg-surface p-4 shadow-subtle">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs font-mono">
              <div
                className={`p-2.5 rounded-xl border transition-all ${
                  !activeProposal
                    ? "bg-accent-surface border-accent/40 text-accent font-bold"
                    : "bg-canvas-subtle border-border text-fg-muted"
                }`}
              >
                <span className="text-[10px] block opacity-70">STEP 01</span>
                <span>User Intent</span>
              </div>

              <div
                className={`p-2.5 rounded-xl border transition-all ${
                  activeProposal
                    ? "bg-accent-surface border-accent/40 text-accent font-bold"
                    : "bg-canvas-subtle border-border text-fg-subtle"
                }`}
              >
                <span className="text-[10px] block opacity-70">STEP 02</span>
                <span>Live Quote</span>
              </div>

              <div
                className={`p-2.5 rounded-xl border transition-all ${
                  activeProposal
                    ? "bg-accent-surface border-accent/40 text-accent font-bold"
                    : "bg-canvas-subtle border-border text-fg-subtle"
                }`}
              >
                <span className="text-[10px] block opacity-70">STEP 03</span>
                <span>Risk Engine</span>
              </div>

              <div
                className={`p-2.5 rounded-xl border transition-all ${
                  activeProposal
                    ? "bg-accent-surface border-accent/40 text-accent font-bold"
                    : "bg-canvas-subtle border-border text-fg-subtle"
                }`}
              >
                <span className="text-[10px] block opacity-70">STEP 04</span>
                <span>Trade Review</span>
              </div>

              <div
                className={`col-span-2 md:col-span-1 p-2.5 rounded-xl border transition-all ${
                  activeProposal?.risk.can_execute
                    ? "bg-accent-surface border-accent/40 text-accent font-bold"
                    : "bg-canvas-subtle border-border text-fg-subtle"
                }`}
              >
                <span className="text-[10px] block opacity-70">STEP 05</span>
                <span>Confirmation</span>
              </div>
            </div>
          </div>

          {/* Interactive Stage: Composer + Review Card */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-5 space-y-4">
              <TradeComposer
                onProposalCreated={(prop) => setActiveProposal(prop)}
              />

              <div className="rounded-xl border border-border bg-canvas-subtle p-4 text-xs text-fg-muted space-y-2">
                <span className="font-semibold text-fg block text-[11px] uppercase tracking-wider font-sans">
                  The Deterministic Rule Invariant
                </span>
                <p className="leading-relaxed text-[11px]">
                  Language models generate suggestions; our Python server calculates balances, limits, and fills. If the risk engine issues a <span className="font-mono text-danger font-bold">BLOCK</span>, no user action or prompt instruction can bypass execution boundaries.
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
                <div className="rounded-2xl border border-dashed border-border bg-surface p-10 sm:p-14 text-center text-fg-subtle flex flex-col items-center justify-center min-h-[420px] shadow-subtle">
                  <div className="h-12 w-12 rounded-xl bg-canvas-subtle border border-border flex items-center justify-center mb-4 text-fg-muted">
                    <FileCheck2 className="h-6 w-6 text-accent" />
                  </div>
                  <h3 className="text-sm font-semibold text-fg">
                    Awaiting Trade Intent
                  </h3>
                  <p className="text-xs text-fg-subtle max-w-sm mt-1.5 leading-relaxed">
                    Select a scenario on the left (e.g. <span className="font-mono text-fg font-medium">“Buy $500 of BTC”</span>) or enter a custom intent to inspect the signature Trade Review card.
                  </p>

                  <div className="mt-6 grid grid-cols-2 gap-2 text-left w-full max-w-md">
                    <div className="rounded-lg border border-border bg-canvas-subtle p-2.5 text-[11px]">
                      <span className="text-fg-subtle block font-mono text-[10px]">CHECK 1</span>
                      <span className="font-medium text-fg">Liquid Cash Balance</span>
                    </div>
                    <div className="rounded-lg border border-border bg-canvas-subtle p-2.5 text-[11px]">
                      <span className="text-fg-subtle block font-mono text-[10px]">CHECK 2</span>
                      <span className="font-medium text-fg">Asset Allowlist</span>
                    </div>
                    <div className="rounded-lg border border-border bg-canvas-subtle p-2.5 text-[11px]">
                      <span className="text-fg-subtle block font-mono text-[10px]">CHECK 3</span>
                      <span className="font-medium text-fg">$25,000 Notional Limit</span>
                    </div>
                    <div className="rounded-lg border border-border bg-canvas-subtle p-2.5 text-[11px]">
                      <span className="text-fg-subtle block font-mono text-[10px]">CHECK 4</span>
                      <span className="font-medium text-fg">40% Concentration</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 3. HOW TRADEGUARD WORKS                                                  */}
        {/* ========================================================================= */}
        <section id="how-it-works" className="space-y-10 scroll-mt-24">
          <div className="text-center space-y-2 max-w-xl mx-auto">
            <span className="text-[11px] font-mono uppercase tracking-wider text-accent font-semibold">
              Execution Architecture
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
              How TradeGuard Works
            </h2>
            <p className="text-xs sm:text-sm text-fg-subtle">
              An unyielding pipeline converting natural language requests into mathematically verified, human-confirmed transactions.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Step 1 */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-canvas-subtle font-mono text-xs font-bold text-fg border border-border">
                01
              </div>
              <h3 className="text-sm font-semibold text-fg">Understand Intent</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Free-form conversational input is extracted into strongly-typed domain models (<span className="font-mono text-[11px]">asset, side, amount, amount_type</span>) and validated against Pydantic schemas.
              </p>
            </div>

            {/* Step 2 */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-canvas-subtle font-mono text-xs font-bold text-fg border border-border">
                02
              </div>
              <h3 className="text-sm font-semibold text-fg">Retrieve Market Context</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Pulls institutional quote snapshots with tight bid-ask spreads, real-time timestamps, and strict 30-second TTL freshness windows before review.
              </p>
            </div>

            {/* Step 3 */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-canvas-subtle font-mono text-xs font-bold text-fg border border-border">
                03
              </div>
              <h3 className="text-sm font-semibold text-fg">Deterministic Risk Verification</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Server-side Python rules evaluate liquid balances, asset allowlists, maximum notional ceilings, and portfolio concentration thresholds.
              </p>
            </div>

            {/* Step 4 */}
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-surface font-mono text-xs font-bold text-accent border border-accent/30">
                04
              </div>
              <h3 className="text-sm font-semibold text-fg">Human Confirmation Gate</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Renders the transparent Trade Review card highlighting before/after exposure. No order reaches True Markets Gateway without explicit human authorization.
              </p>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 4. WHY THE PRE-TRADE SAFETY LAYER MATTERS                                */}
        {/* ========================================================================= */}
        <section id="safety-layer" className="space-y-10 scroll-mt-24">
          <div className="text-center space-y-2 max-w-xl mx-auto">
            <span className="text-[11px] font-mono uppercase tracking-wider text-accent font-semibold">
              The Safety Imperative
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
              Why the Pre-Trade Safety Layer Matters
            </h2>
            <p className="text-xs sm:text-sm text-fg-subtle">
              Large language models should propose, never execute. TradeGuard enforces a strict architectural firewall between language models and money.
            </p>
          </div>

          <div className="rounded-2xl border border-border bg-surface overflow-hidden shadow-card">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-canvas-subtle text-[11px] font-semibold text-fg-muted">
                    <th className="py-3.5 px-6">Risk Dimension</th>
                    <th className="py-3.5 px-6 text-danger">Unchecked AI Execution</th>
                    <th className="py-3.5 px-6 text-accent">TradeGuard Safety Boundary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  <tr>
                    <td className="py-4 px-6 font-semibold text-fg">Execution Authority</td>
                    <td className="py-4 px-6 text-fg-muted">Model autonomously submits orders to exchange APIs directly.</td>
                    <td className="py-4 px-6 text-fg font-medium">Zero autonomous execution; explicit human cryptographic authorization required.</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 font-semibold text-fg">Financial Math & Sizing</td>
                    <td className="py-4 px-6 text-fg-muted">Probabilistic LLM math prone to hallucinated fill prices and quantity errors.</td>
                    <td className="py-4 px-6 text-fg font-medium">Deterministic server-side Python math using live True Markets quote feeds.</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 font-semibold text-fg">Balance & Liquidity Checks</td>
                    <td className="py-4 px-6 text-fg-muted">Assumes purchasing power from chat memory; prone to overdrawing or liquidation.</td>
                    <td className="py-4 px-6 text-fg font-medium">Authoritative database & gateway balance queries enforce strict cash adequacy.</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 font-semibold text-fg">Prompt Injection Defense</td>
                    <td className="py-4 px-6 text-fg-muted">Malicious prompt injection can override instructions and drain balances.</td>
                    <td className="py-4 px-6 text-fg font-medium">Hardcoded server invariants ($25k ceilings, allowlists) cannot be bypassed by prompts.</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 font-semibold text-fg">Auditability & Compliance</td>
                    <td className="py-4 px-6 text-fg-muted">Ephemeral chat transcripts with no verifiable state transitions.</td>
                    <td className="py-4 px-6 text-fg font-medium">Immutable, chronologically timestamped audit trail with full event metadata.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 5. PRODUCT CAPABILITIES                                                  */}
        {/* ========================================================================= */}
        <section id="capabilities" className="space-y-10 scroll-mt-24">
          <div className="text-center space-y-2 max-w-xl mx-auto">
            <span className="text-[11px] font-mono uppercase tracking-wider text-accent font-semibold">
              Platform Features
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
              Institutional Product Capabilities
            </h2>
            <p className="text-xs sm:text-sm text-fg-subtle">
              Engineered with fintech-grade precision, complete transparency, and zero fluff.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-canvas-subtle border border-border text-accent">
                <Terminal className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-fg">Structured Intent Extraction</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Transforms conversational sentences into validated schemas with asset resolution, side detection, and quantity type inference.
              </p>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-canvas-subtle border border-border text-accent">
                <Clock className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-fg">Live Quoting with 30s TTL</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Tight institutional spreads with timestamp verification. Stale quotes expire automatically to prevent slippage in volatile markets.
              </p>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-canvas-subtle border border-border text-accent">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-fg">Deterministic Guardrails</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                4-layer server verification yielding clear PASS, WARN, or BLOCK statuses: cash check, allowlist, max notional, and concentration.
              </p>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-canvas-subtle border border-border text-accent">
                <PieChart className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-fg">Portfolio Impact Simulation</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Calculates before and after asset allocation percentages and liquid cash debits before the trade is submitted.
              </p>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-canvas-subtle border border-border text-accent">
                <FileText className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-fg">Immutable Cryptographic Audit</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Every prompt, quote snapshot, risk evaluation, and order fulfillment is permanently appended to a queryable chronological audit stream.
              </p>
            </div>

            <div className="rounded-2xl border border-border bg-surface p-6 shadow-card space-y-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-canvas-subtle border border-border text-accent">
                <Activity className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-fg">True Markets Gateway Integration</h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Connects directly to True Markets Retail Gateway (<span className="font-mono text-[10px]">api.uat.truemarkets.co</span>) with isolated signer key signing.
              </p>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 6. SECURITY & ARCHITECTURE                                               */}
        {/* ========================================================================= */}
        <section id="security" className="rounded-3xl border border-border bg-surface p-6 sm:p-10 shadow-card space-y-8 scroll-mt-24">
          <div className="max-w-2xl space-y-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-accent font-semibold">
              System Architecture & Trust Guarantees
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
              Zero-Trust Financial Architecture
            </h2>
            <p className="text-xs sm:text-sm text-fg-subtle">
              Engineered with institutional separation of duties: language models propose, Python code governs, humans confirm, True Markets executes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-xl border border-border bg-canvas-subtle p-5 space-y-3">
              <div className="flex items-center gap-2 text-fg font-semibold text-sm">
                <Lock className="h-4 w-4 text-accent" />
                <span>Zero Direct Model Execution</span>
              </div>
              <p className="text-xs text-fg-muted leading-relaxed">
                The language model has zero write privileges to True Markets Gateway endpoints or wallet balances. Every order requires explicit human signature.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-canvas-subtle p-5 space-y-3">
              <div className="flex items-center gap-2 text-fg font-semibold text-sm">
                <ShieldAlert className="h-4 w-4 text-accent" />
                <span>Deterministic Code Overrides</span>
              </div>
              <p className="text-xs text-fg-muted leading-relaxed">
                Authoritative numbers and balance checks are owned exclusively by server-side Python code. A <span className="font-mono text-danger font-bold">BLOCK</span> status can never be overridden.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-canvas-subtle p-5 space-y-3">
              <div className="flex items-center gap-2 text-fg font-semibold text-sm">
                <KeyRound className="h-4 w-4 text-accent" />
                <span>Backend Credential Isolation</span>
              </div>
              <p className="text-xs text-fg-muted leading-relaxed">
                True Markets Organization API keys and local private signer keys are strictly backend-only and never reach the client bundle or browser.
              </p>
            </div>
          </div>

          {/* Architecture Pipeline Map */}
          <div className="rounded-xl border border-border bg-canvas-subtle p-4 font-mono text-xs space-y-2">
            <span className="text-[10px] uppercase font-bold text-fg-subtle tracking-wider font-sans block">
              Gateway Endpoint Routing
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-[11px] text-fg-muted">
              <div className="p-2 rounded bg-surface border border-border">
                <span className="text-accent font-semibold">POST</span> /quotes
              </div>
              <div className="p-2 rounded bg-surface border border-border">
                <span className="text-accent font-semibold">POST</span> /orders
              </div>
              <div className="p-2 rounded bg-surface border border-border">
                <span className="text-accent font-semibold">POST</span> /orders/&#123;id&#125;/execute
              </div>
              <div className="p-2 rounded bg-surface border border-border">
                <span className="text-accent font-semibold">GET</span> /orders/&#123;id&#125;/status
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 7. FINAL CALL TO ACTION                                                  */}
        {/* ========================================================================= */}
        <section className="text-center space-y-5 py-8 sm:py-12">
          <div className="space-y-2 max-w-lg mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fg">
              Ready to trade with total control?
            </h2>
            <p className="text-xs sm:text-sm text-fg-subtle">
              Experience TradeGuard in simulated demo mode with pre-seeded balances or configure live True Markets UAT credentials.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              href="/app"
              className="inline-flex items-center gap-2 rounded-xl bg-accent px-6 py-3.5 text-sm font-semibold text-white shadow-subtle hover:bg-accent-dark transition-all"
            >
              <span>Launch Application</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/app/portfolio"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-6 py-3.5 text-sm font-semibold text-fg hover:bg-surface-hover transition-all shadow-subtle"
            >
              <span>Explore Portfolio</span>
            </Link>
          </div>
        </section>
      </main>

      {/* ========================================================================= */}
      {/* 8. FOOTER                                                                */}
      {/* ========================================================================= */}
      <footer className="border-t border-border bg-surface py-10 text-xs text-fg-subtle transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <Image
                src="/branding/tradeguard-logo.svg"
                alt="TradeGuard"
                width={18}
                height={18}
              />
              <span className="font-semibold text-fg text-sm">
                TradeGuard
              </span>
              <span className="text-fg-subtle font-mono text-[11px]">
                — Think before you trade.
              </span>
            </div>

            <div className="flex items-center gap-5 text-xs text-fg-muted font-medium">
              <Link href="/app" className="hover:text-fg transition-colors">
                Dashboard
              </Link>
              <Link href="/app/trade" className="hover:text-fg transition-colors">
                Trade
              </Link>
              <Link href="/app/portfolio" className="hover:text-fg transition-colors">
                Portfolio
              </Link>
              <Link href="/app/activity" className="hover:text-fg transition-colors">
                Audit Trail
              </Link>
              <a href="#security" className="hover:text-fg transition-colors">
                Security
              </a>
            </div>
          </div>

          <div className="pt-4 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-fg-subtle">
            <span>
              Built for the True Markets “Build the Next Wealth App” Challenge.
            </span>
            <span className="font-mono">
              Deterministic Gate · Zero Autonomous Execution Invariant
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
