import {
  AuditEvent,
  OrderRecord,
  ParsedIntent,
  PortfolioSummary,
  TradeProposal,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  let url = `${API_BASE_URL}${endpoint}`;
  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    });
  } catch (err) {
    // If absolute URL failed (e.g. CORS or network), try relative /api path forwarded by Next.js rewrites
    if (API_BASE_URL.startsWith("http")) {
      url = `/api${endpoint}`;
      res = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...(options?.headers || {}),
        },
      });
    } else {
      throw err;
    }
  }

  if (!res.ok) {
    // If got 404 on absolute URL, try relative /api fallback once
    if (res.status === 404 && API_BASE_URL.startsWith("http")) {
      try {
        const fallbackRes = await fetch(`/api${endpoint}`, {
          ...options,
          headers: {
            "Content-Type": "application/json",
            ...(options?.headers || {}),
          },
        });
        if (fallbackRes.ok) {
          return fallbackRes.json() as Promise<T>;
        }
      } catch {
        // ignore fallback error
      }
    }

    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
}

export const api = {
  getHealth: () => fetchJson<{ status: string; true_markets_mode: string }>("/health"),

  parseIntent: (prompt: string) =>
    fetchJson<ParsedIntent>("/intent/parse", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),

  createProposal: (prompt: string) =>
    fetchJson<TradeProposal>("/trades/proposals", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),

  createStructuredProposal: (asset: string, side: "BUY" | "SELL", amount: number, amount_type: "USD" | "ASSET") =>
    fetchJson<TradeProposal>("/trades/proposals", {
      method: "POST",
      body: JSON.stringify({ asset, side, amount, amount_type }),
    }),

  getProposal: (proposalId: string) =>
    fetchJson<TradeProposal>(`/trades/proposals/${proposalId}`),

  confirmTrade: (proposalId: string) =>
    fetchJson<OrderRecord>(`/trades/${proposalId}/confirm`, {
      method: "POST",
    }),

  cancelTrade: (proposalId: string) =>
    fetchJson<{ status: string }>(`/trades/${proposalId}/cancel`, {
      method: "POST",
    }),

  getOrder: (orderId: string) => fetchJson<OrderRecord>(`/orders/${orderId}`),

  getPortfolio: () => fetchJson<PortfolioSummary>("/portfolio"),

  getActivity: (limit = 50) => fetchJson<AuditEvent[]>(`/activity?limit=${limit}`),

  resetDemo: async () => {
    try {
      return await fetchJson<{ message: string }>("/system/reset-demo", {
        method: "POST",
      });
    } catch {
      try {
        return await fetchJson<{ message: string }>("/reset-demo", {
          method: "POST",
        });
      } catch {
        return await fetchJson<{ message: string }>("/reset", {
          method: "POST",
        });
      }
    }
  },
};
