"use client";

import React, { useState } from "react";
import { Play, Pause, RotateCcw, CheckCircle2, Shield, Lock, ArrowRight } from "lucide-react";

export function DemoVideoSection() {
  const [activeStep, setActiveStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const steps = [
    {
      time: "0:00 – 0:15",
      title: "Landing & Value Proposition",
      description:
        "“TradeGuard is an AI-assisted execution layer designed to help users think before they trade.”",
      preview: "Clean, restrained fintech interface. Apple-level typography and Linear-level product polish.",
    },
    {
      time: "0:15 – 0:35",
      title: "Natural Language Intent",
      description: "User inputs: “Buy $500 of BTC” into the composer.",
      preview: "Backend validates structured intent: { asset: 'BTC', side: 'BUY', amount: 500, amount_type: 'USD' }.",
    },
    {
      time: "0:35 – 1:05",
      title: "Live Quote & Deterministic Risk Analysis",
      description:
        "Real-time BTC/USDC quote retrieved. 5 deterministic risk checks run server-side.",
      preview: "Calculated: 0.005784 BTC at $86,471.61 USDC. Balance: PASS, Supported: PASS, Max Limit: PASS, Concentration: WARN (47.1%).",
    },
    {
      time: "1:05 – 1:30",
      title: "Human Confirmation Gate",
      description:
        "Signature Trade Review card presented. AI analysis cannot execute directly.",
      preview: "User explicitly verifies quote spread and exposure shift before clicking 'Confirm Trade'.",
    },
    {
      time: "1:30 – 1:55",
      title: "True Markets Execution Lifecycle",
      description:
        "Order created, signed, and dispatched to True Markets Gateway.",
      preview: "External order ID assigned: tm-sim-74f9e1a8. Order lifecycle moves from SUBMITTED to FILLED.",
    },
    {
      time: "1:55 – 2:20",
      title: "Portfolio & Immutable Audit Trail",
      description:
        "Cash balance debited, BTC holding credited, immutable audit event recorded.",
      preview: "Cash: $10,000.00 → $9,500.00. Chronological audit stream logged with cryptographically verifiable timestamps.",
    },
    {
      time: "2:20 – 2:40",
      title: "Architecture & Security Boundary",
      description:
        "Secrets backend-only. Zero LLM hallucinations touching fund balances.",
      preview: "Next.js → FastAPI → Deterministic Risk Engine → True Markets Client Adapter.",
    },
    {
      time: "2:40 – 2:55",
      title: "Closing",
      description: "“TradeGuard — Think before you trade.”",
      preview: "Production-ready, auditable execution engine ready for the True Markets ecosystem.",
    },
  ];

  return (
    <div className="w-full rounded-3xl border border-border bg-surface p-6 sm:p-10 shadow-elevated">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border">
        <div>
          <span className="rounded-full bg-emerald-surface px-3 py-1 font-mono text-xs font-semibold text-emerald border border-emerald/20">
            VIDEO WALKTHROUGH · 2:55 RUNTIME
          </span>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-fg">
            The 2-Minute TradeGuard Story
          </h2>
          <p className="text-xs text-fg-subtle mt-1">
            Follow the exact judge evaluation flow from prompt to True Markets execution
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveStep((prev) => Math.max(0, prev - 1))}
            disabled={activeStep === 0}
            className="rounded-lg border border-border bg-canvas-subtle px-3 py-1.5 text-xs text-fg disabled:opacity-40"
          >
            Prev
          </button>
          <span className="font-mono text-xs font-semibold text-fg">
            {activeStep + 1} / {steps.length}
          </span>
          <button
            onClick={() =>
              setActiveStep((prev) => Math.min(steps.length - 1, prev + 1))
            }
            disabled={activeStep === steps.length - 1}
            className="rounded-lg border border-border bg-canvas-subtle px-3 py-1.5 text-xs text-fg disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>

      {/* Main Video Stage Demonstration */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Step List */}
        <div className="space-y-2">
          {steps.map((st, i) => (
            <button
              key={i}
              onClick={() => setActiveStep(i)}
              className={`w-full text-left rounded-xl p-3 text-xs transition-all border ${
                activeStep === i
                  ? "bg-surface-elevated border-emerald/50 shadow-sm"
                  : "border-transparent hover:bg-surface-hover text-fg-muted"
              }`}
            >
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span
                  className={activeStep === i ? "text-emerald font-bold" : "text-fg-subtle"}
                >
                  {st.time}
                </span>
                {activeStep === i && (
                  <span className="flex h-1.5 w-1.5 rounded-full bg-emerald" />
                )}
              </div>
              <h4
                className={`mt-1 font-semibold ${
                  activeStep === i ? "text-fg" : "text-fg-muted"
                }`}
              >
                {st.title}
              </h4>
            </button>
          ))}
        </div>

        {/* Active Stage Screen Preview */}
        <div className="lg:col-span-2 rounded-2xl border border-border bg-canvas-subtle p-6 sm:p-8 relative overflow-hidden">
          <div className="flex items-center justify-between pb-4 border-b border-border text-xs">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald" />
              <span className="font-mono font-medium text-fg">
                Scene: {steps[activeStep].time}
              </span>
            </div>
            <span className="text-fg-subtle font-mono text-[11px]">
              TradeGuard Simulator Stage
            </span>
          </div>

          <div className="mt-6 space-y-4">
            <h3 className="text-xl font-bold text-fg">
              {steps[activeStep].title}
            </h3>
            <blockquote className="rounded-xl border-l-2 border-emerald bg-surface p-4 text-sm italic text-fg leading-relaxed">
              {steps[activeStep].description}
            </blockquote>

            <div className="rounded-xl border border-border bg-surface p-4 text-xs font-mono">
              <span className="text-[10px] uppercase font-bold text-fg-subtle tracking-wider block mb-1">
                System Action
              </span>
              <p className="text-emerald font-medium">
                {steps[activeStep].preview}
              </p>
            </div>
          </div>

          {/* Interactive Navigation inside screen */}
          <div className="mt-8 flex items-center justify-between pt-4 border-t border-border">
            <span className="text-[11px] text-fg-subtle">
              Step {activeStep + 1} of {steps.length}
            </span>
            {activeStep < steps.length - 1 ? (
              <button
                onClick={() => setActiveStep(activeStep + 1)}
                className="flex items-center gap-1 text-xs font-semibold text-emerald hover:text-emerald-dark"
              >
                <span>Continue to Next Scene</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            ) : (
              <span className="text-xs font-semibold text-emerald">
                Story complete · Ready to trade
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
