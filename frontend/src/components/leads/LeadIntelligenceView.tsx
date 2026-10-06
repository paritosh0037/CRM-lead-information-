"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchLeadIntelligence, fetchRankedLeads } from "@/lib/api";
import LeadHeader from "./LeadHeader";
import LeadScoreCard from "./LeadScoreCard";
import RecommendationCard from "./RecommendationCard";
import ExplanationCard from "./ExplanationCard";
import InteractionTimeline from "./InteractionTimeline";
import LeadContextCard from "./LeadContextCard";
import { AlertCircle } from "lucide-react";

export default function LeadIntelligenceView({ leadId }: { leadId: string }) {
  // Fetch intelligence data
  const { 
    data: intel, 
    isLoading: isIntelLoading, 
    isError: isIntelError,
    error: intelError,
    refetch 
  } = useQuery({
    queryKey: ["lead-intel", leadId],
    queryFn: () => fetchLeadIntelligence(leadId),
    retry: 1,
  });

  // Fetch Ranked Leads to get CRM context fields (opportunistic query)
  const { data: rankedLeads } = useQuery({
    queryKey: ["leads", "ranked"],
    queryFn: () => fetchRankedLeads(1000, 0),
    staleTime: 60 * 1000,
  });

  const leadInfo = rankedLeads?.leads.find(l => l.lead_id === leadId) || null;

  if (isIntelLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-20 bg-line-100 rounded-md"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-40 bg-line-100 rounded-md"></div>
          <div className="h-40 bg-line-100 rounded-md"></div>
          <div className="h-40 bg-line-100 rounded-md"></div>
        </div>
        <div className="h-96 bg-line-100 rounded-md"></div>
      </div>
    );
  }

  if (isIntelError || !intel) {
    return (
      <div className="bg-flag-50 border border-flag-200 p-8 rounded-md flex flex-col items-center justify-center text-center h-64">
        <AlertCircle className="w-8 h-8 text-flag-600 mb-4" />
        <h3 className="font-medium text-lg text-flag-700 mb-2">Failed to load lead intelligence</h3>
        <p className="text-sm text-flag-600 mb-6 max-w-md">
          {intelError instanceof Error ? intelError.message : "The backend could not process this request or the lead was not found."}
        </p>
        <button 
          onClick={() => refetch()}
          className="px-4 py-2 bg-white border border-flag-300 rounded-md text-sm font-medium hover:bg-flag-50 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <LeadHeader leadId={leadId} />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <LeadScoreCard 
          score={intel.lead_score} 
          probability={intel.conversion_probability} 
        />
        <RecommendationCard 
          leadId={leadId}
          action={intel.recommendation.recommended_action} 
          confidence={intel.recommendation.recommendation_confidence} 
        />
        <LeadContextCard leadInfo={leadInfo} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ExplanationCard 
            explanation={intel.explanation} 
            rationale={intel.recommendation.rationale} 
          />
        </div>
        <div>
          <InteractionTimeline leadId={leadId} />
        </div>
      </div>
    </div>
  );
}
