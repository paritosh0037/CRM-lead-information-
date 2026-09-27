export interface LeadScoreResponse {
  lead_id: string;
  conversion_probability: number;
  lead_score: number;
}

export interface FactorDetail {
  feature: string;
  display_name: string;
  impact: number;
  raw_value: any;
}

export interface LeadExplanationResponse {
  lead_id: string;
  lead_score: number;
  conversion_probability: number;
  base_value: number;
  positive_factors: FactorDetail[];
  negative_factors: FactorDetail[];
  top_factors: FactorDetail[];
  explanation_text: string;
}

export interface RuleTrace {
  score_band: string;
  trigger: string;
  action: string;
}

export interface LeadRecommendationResponse {
  lead_id: string;
  lead_score: number;
  conversion_probability: number;
  recommended_action: string;
  recommendation_confidence: number;
  confidence_reasons: string[];
  rationale: string;
  rule_trace: RuleTrace;
}

export interface CombinedLeadIntelligenceResponse {
  lead_id: string;
  conversion_probability: number;
  lead_score: number;
  explanation: LeadExplanationResponse;
  recommendation: LeadRecommendationResponse;
}

export interface RankedLeadItem {
  lead_id: string;
  lead_score: number;
  conversion_probability: number;
  recommended_action: string;
  recommendation_confidence: number;
  opportunity_stage?: string;
  deal_value?: number;
  company_size?: string;
  industry?: string;
}

export interface RankedLeadsResponse {
  total: number;
  limit: number;
  offset: number;
  leads: RankedLeadItem[];
}

export interface FeedbackResponse {
  id: number;
  lead_id: string;
  original_action: string;
  override_action?: string;
  reason?: string;
  timestamp: string;
}

export interface AnalyticsResponse {
  total_leads: number;
  high_priority_leads: number;
  pipeline_value: number;
  average_lead_score: number;
  score_distribution: Record<string, number>;
  score_by_opportunity_stage: Record<string, number>;
  action_distribution: Record<string, number>;
}
