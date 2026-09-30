"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import { TradeProposal } from "@/lib/types";
import { ArrowRight, Sparkles, AlertCircle } from "lucide-react";

interface TradeComposerProps {
  onProposalCreated: (proposal: TradeProposal) => void;
}

export function TradeComposer({ onProposalCreated }: TradeComposerProps) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const samplePrompts = [
    { label: "Core Demo", text: "Buy $500 of BTC" },
    { label: "Acquire ETH", text: "Buy $1,200 of ETH" },
    { label: "Sell BTC", text: "Sell 0.05 BTC" },
    { label: "Test Max Limit (Block)", text: "Buy $30,000 of BTC" },
    { label: "Test Balance (Block)", text: "Buy $18,000 of SOL" },
    { label: "Unsupported (Block)", text: "Buy $500 of DOGE" },
  ];

  const handleSubmit = async (textToSubmit?: string) => {
    const text = (textToSubmit || prompt).trim();
    if (!text) return;
    try {
      setLoading(true);
      setError(null);
      const proposal = await api.createProposal(text);
      onProposalCreated(proposal);
    } catch (err: any) {
      setError(err.message || "Failed to create trade proposal.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full rounded-2xl border border-border bg-surface p-6 shadow-card transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-surface text-emerald">
            <Sparkles className="h-4 w-4" />
          </div>
          <h3 className="text-sm font-semibold text-fg">
            Trade Intent Composer
          </h3>
        </div>
        <span className="text-[11px] text-fg-subtle">
          Natural Language → Deterministic Proposal
        </span>
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        className="space-y-3"
      >
        <div className="relative">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Buy $500 of BTC or Sell 1.5 ETH..."
            disabled={loading}
            className="w-full rounded-xl border border-border bg-canvas-subtle px-4 py-3.5 pr-28 text-sm text-fg placeholder:text-fg-subtle focus:border-emerald focus:outline-none focus:ring-1 focus:ring-emerald transition-all"
          />
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="absolute right-2 top-2 bottom-2 rounded-lg bg-emerald px-3.5 text-xs font-semibold text-white hover:bg-emerald-dark disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-1.5"
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

        {error && (
          <div className="rounded-lg border border-danger/30 bg-danger-surface p-2.5 text-xs text-danger flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </form>

      {/* Curated Sample Prompts for Instant Testing */}
      <div className="mt-4 pt-4 border-t border-border">
        <span className="text-[11px] font-medium text-fg-subtle block mb-2">
          1-Click Review Prompts:
        </span>
        <div className="flex flex-wrap gap-2">
          {samplePrompts.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setPrompt(item.text);
                handleSubmit(item.text);
              }}
              disabled={loading}
              className="rounded-lg border border-border bg-canvas-subtle px-2.5 py-1.5 text-xs text-fg-muted hover:border-emerald hover:text-fg transition-all text-left"
            >
              <span className="font-semibold text-fg block text-[10px]">
                {item.label}
              </span>
              <span className="text-[11px] font-mono text-fg-subtle">
                {item.text}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
