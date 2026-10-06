import { 
  RankedLeadsResponse, 
  CombinedLeadIntelligenceResponse,
  FeedbackResponse,
  AnalyticsResponse,
  InteractionResponse
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export async function fetchRankedLeads(limit = 50, offset = 0): Promise<RankedLeadsResponse> {
  const res = await fetch(`${API_BASE_URL}/leads/ranked?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch ranked leads");
  return res.json();
}

export async function fetchLeadIntelligence(leadId: string): Promise<CombinedLeadIntelligenceResponse> {
  const res = await fetch(`${API_BASE_URL}/leads/${leadId}`);
  if (!res.ok) throw new Error("Failed to fetch lead intelligence");
  return res.json();
}

export async function fetchLeadFeedback(leadId: string): Promise<FeedbackResponse[]> {
  const res = await fetch(`${API_BASE_URL}/feedback/${leadId}`);
  if (!res.ok) throw new Error("Failed to fetch lead feedback");
  return res.json();
}

export async function acceptRecommendation(leadId: string, originalAction: string): Promise<FeedbackResponse> {
  const res = await fetch(`${API_BASE_URL}/feedback/${leadId}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ original_action: originalAction }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to accept recommendation");
  }
  return res.json();
}

export async function overrideRecommendation(
  leadId: string, 
  originalAction: string, 
  overrideAction: string, 
  reason: string
): Promise<FeedbackResponse> {
  const res = await fetch(`${API_BASE_URL}/feedback/${leadId}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      original_action: originalAction,
      override_action: overrideAction,
      reason
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to override recommendation");
  }
  return res.json();
}

export async function fetchAnalytics(): Promise<AnalyticsResponse> {
  const res = await fetch(`${API_BASE_URL}/analytics`);
  if (!res.ok) throw new Error("Failed to fetch analytics");
  return res.json();
}

export async function fetchLeadInteractions(leadId: string): Promise<InteractionResponse[]> {
  const res = await fetch(`${API_BASE_URL}/leads/${leadId}/interactions`);
  if (!res.ok) throw new Error("Failed to fetch lead interactions");
  return res.json();
}

