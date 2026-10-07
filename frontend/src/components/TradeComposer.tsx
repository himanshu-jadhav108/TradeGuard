"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import { TradeProposal } from "@/lib/types";
import { ArrowRight, Terminal, AlertCircle, HelpCircle } from "lucide-react";

interface TradeComposerProps {
  onProposalCreated: (proposal: TradeProposal) => void;
}

export function TradeComposer({ onProposalCreated }: TradeComposerProps) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [stageText, setStageText] = useState("Interpreting intent...");
  const [error, setError] = useState<string | null>(null);
  const [clarificationSuggestions, setClarificationSuggestions] = useState<string[]>([]);

  const samplePrompts = [
    {
      category: "PASS",
      label: "Standard Intent",
      text: "Buy $500 of SOL",
      badgeColor: "text-accent bg-accent-surface border-accent/20",
    },
    {
      category: "WARN",
      label: "Concentration Limit",
      text: "Buy $5,000 of BTC",
      badgeColor: "text-warn bg-warn-surface border-warn/20",
    },
    {
      category: "BLOCK",
      label: "Max Notional Ceiling",
      text: "Buy $30,000 of BTC",
      badgeColor: "text-danger bg-danger-surface border-danger/20",
    },
    {
      category: "BLOCK",
      label: "Insufficient Balance",
      text: "Buy $15,000 of ETH",
      badgeColor: "text-danger bg-danger-surface border-danger/20",
    },
    {
      category: "BLOCK",
      label: "Unsupported Asset",
      text: "Buy $500 of DOGE",
      badgeColor: "text-danger bg-danger-surface border-danger/20",
    },
  ];

  const handleSubmit = async (textToSubmit?: string) => {
    const text = (textToSubmit || prompt).trim();
    if (!text) return;
    try {
      setLoading(true);
      setStageText("Interpreting intent...");
      setError(null);
      setClarificationSuggestions([]);

      const timer1 = setTimeout(() => setStageText("Fetching quote..."), 150);
      const timer2 = setTimeout(() => setStageText("Running risk checks..."), 320);

      const proposal = await api.createProposal(text);
      clearTimeout(timer1);
      clearTimeout(timer2);
      onProposalCreated(proposal);
    } catch (err: any) {
      setError(err.message || "Failed to create trade proposal.");
      // Check for suggestions from intent parser
      try {
        const parseCheck = await api.parseIntent(text);
        if (parseCheck.suggestions && parseCheck.suggestions.length > 0) {
          setClarificationSuggestions(parseCheck.suggestions);
        }
      } catch {
        // ignore parse check secondary error
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="w-full rounded-2xl border border-border bg-surface p-5 sm:p-6 shadow-card transition-all"
      suppressHydrationWarning
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-canvas-subtle border border-border text-fg-muted">
            <Terminal className="h-3.5 w-3.5 text-accent" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-fg">
              Natural Language Intent
            </h3>
          </div>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-wider text-fg-subtle">
          Rule-Based Intent Interpreter
        </span>
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        autoComplete="off"
        data-lpignore="true"
        data-1p-ignore="true"
        data-form-type="other"
        className="space-y-3"
        suppressHydrationWarning
      >
        <div className="relative">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Buy $500 of BTC or Sell 0.05 BTC..."
            disabled={loading}
            autoComplete="off"
            data-lpignore="true"
            data-1p-ignore="true"
            data-form-type="other"
            suppressHydrationWarning
            className="w-full rounded-xl border border-border bg-canvas-subtle px-4 py-3.5 pr-28 text-sm text-fg placeholder:text-fg-subtle focus:border-accent focus:bg-surface focus:outline-none focus:ring-1 focus:ring-accent transition-all font-sans"
          />
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            suppressHydrationWarning
            className="absolute right-2 top-2 bottom-2 rounded-lg bg-accent px-3.5 text-xs font-semibold text-white hover:bg-accent-dark disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center gap-1.5 shadow-subtle"
          >
            {loading ? (
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <>
                <span>Review</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </>
            )}
          </button>
        </div>

        {loading && (
          <div className="flex items-center justify-between text-xs text-accent font-mono px-2.5 py-1.5 rounded-lg bg-accent-surface/60 border border-accent/20 animate-fadeIn">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
              <span className="font-medium text-accent">{stageText}</span>
            </div>
            <span className="text-[10px] text-fg-subtle">Safety Pipeline</span>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-danger/30 bg-danger-surface p-3.5 text-xs text-danger space-y-2">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-danger mt-0.5" />
              <div className="flex-1 font-sans">
                <span className="font-semibold block">Intent Validation Error</span>
                <span className="text-[11px] leading-relaxed text-danger-text">{error}</span>
              </div>
            </div>

            {clarificationSuggestions.length > 0 && (
              <div className="pt-2 border-t border-danger/20">
                <div className="flex items-center gap-1 text-[11px] font-medium text-danger mb-1.5">
                  <HelpCircle className="h-3 w-3" />
                  <span>Did you mean one of these unambiguous trades?</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {clarificationSuggestions.map((sug, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => {
                        setPrompt(sug);
                        handleSubmit(sug);
                      }}
                      className="rounded-lg bg-surface border border-danger/30 px-2.5 py-1 text-[11px] font-mono text-fg hover:border-accent transition-colors"
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </form>

      {/* Curated Test Scenarios */}
      <div className="mt-5 pt-4 border-t border-border" suppressHydrationWarning>
        <span className="text-[11px] font-medium text-fg-muted block mb-2.5">
          Select test scenario:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2" suppressHydrationWarning>
          {samplePrompts.map((item, idx) => (
            <button
              key={idx}
              type="button"
              suppressHydrationWarning
              onClick={() => {
                setPrompt(item.text);
                handleSubmit(item.text);
              }}
              disabled={loading}
              className="flex items-center justify-between rounded-lg border border-border bg-canvas-subtle p-2.5 text-left text-xs hover:border-accent/50 hover:bg-surface transition-all group"
            >
              <div className="truncate pr-2">
                <span className="text-[11px] font-semibold text-fg block truncate">
                  {item.label}
                </span>
                <span className="font-mono text-[11px] text-fg-subtle block truncate group-hover:text-fg transition-colors">
                  “{item.text}”
                </span>
              </div>
              <span
                className={`shrink-0 rounded px-1.5 py-0.5 font-mono text-[10px] font-bold border ${item.badgeColor}`}
              >
                {item.category}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
