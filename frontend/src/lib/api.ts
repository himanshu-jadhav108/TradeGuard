import {
  AuditEvent,
  IntentParseResponse,
  OrderRecord,
  PortfolioSummary,
  SafetySignalsReport,
  SessionResetResponse,
  TradeProposal,
} from "./types";

export function getSessionId(): string {
  if (typeof window === "undefined") return "demo-user-1";
  let sid = localStorage.getItem("tradeguard_session_id");
  if (!sid || sid.trim().length < 4) {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      sid = "sess-" + crypto.randomUUID();
    } else {
      sid = "sess-" + Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 10);
    }
    localStorage.setItem("tradeguard_session_id", sid);
  }
  return sid;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "/api";

async function fetchJson<T>(
  endpoint: string,
  options?: RequestInit,
  isRetryable: boolean = false
): Promise<T> {
  const sessionId = getSessionId();
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  
  // Use relative /api endpoint directly if API_BASE_URL is relative or default
  const base = API_BASE_URL.replace(/\/+$/, "");
  const url = base.endsWith("/api") && cleanEndpoint.startsWith("/api")
    ? `${base}${cleanEndpoint.replace(/^\/api/, "")}`
    : `${base}${cleanEndpoint}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Session-ID": sessionId,
    ...(options?.headers as Record<string, string> || {}),
  };

  const executeFetch = async () => {
    return fetch(url, {
      ...options,
      headers,
    });
  };

  let res: Response;
  try {
    res = await executeFetch();
  } catch (err: any) {
    // Only safe GET requests can be retried once on transient network failure
    if (isRetryable && (!options?.method || options.method === "GET")) {
      try {
        res = await executeFetch();
      } catch {
        throw new Error(err.message || "Network error connecting to TradeGuard API.");
      }
    } else {
      throw new Error(err.message || "Network error connecting to TradeGuard API.");
    }
  }

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      if (res.status === 502 || res.status === 503) {
        errorDetail = "TradeGuard backend service is currently unavailable. Please ensure the backend server is running.";
      } else if (res.status === 404) {
        errorDetail = "Requested resource not found.";
      }
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
}

export const api = {
  getHealth: () =>
    fetchJson<{
      status: string;
      mode?: string;
      true_markets_mode: string;
      true_markets_configured: boolean;
      true_markets_available?: boolean;
      supported_assets: string[];
    }>("/health", undefined, true),

  parseIntent: (prompt: string) =>
    fetchJson<IntentParseResponse>("/intent/parse", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),

  createProposal: (prompt: string) =>
    fetchJson<TradeProposal>("/trades/proposals", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),

  createStructuredProposal: (
    asset: string,
    side: "BUY" | "SELL",
    amount: number,
    amount_type: "USD" | "ASSET"
  ) =>
    fetchJson<TradeProposal>("/trades/proposals", {
      method: "POST",
      body: JSON.stringify({ asset, side, amount, amount_type }),
    }),

  getProposal: (proposalId: string) =>
    fetchJson<TradeProposal>(`/trades/proposals/${proposalId}`, undefined, true),

  confirmTrade: (proposalId: string, acknowledgedWarnings: boolean = false) =>
    fetchJson<OrderRecord>(`/trades/${proposalId}/confirm`, {
      method: "POST",
      body: JSON.stringify({
        proposal_id: proposalId,
        acknowledged_warnings: acknowledgedWarnings,
      }),
    }),

  cancelTrade: (proposalId: string) =>
    fetchJson<{ status: string; proposal_id: string }>(`/trades/${proposalId}/cancel`, {
      method: "POST",
    }),

  getOrder: (orderId: string) =>
    fetchJson<OrderRecord>(`/orders/${orderId}`, undefined, true),

  getPortfolio: () =>
    fetchJson<PortfolioSummary>("/portfolio", undefined, true),

  getActivity: (limit = 50) =>
    fetchJson<AuditEvent[]>(`/activity?limit=${limit}`, undefined, true),

  getSafetySignals: () =>
    fetchJson<SafetySignalsReport>("/safety-signals", undefined, true),

  resetDemo: () =>
    fetchJson<SessionResetResponse>("/session/reset", {
      method: "POST",
    }),
};
