"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchLeadIntelligence, fetchLeadFeedback } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { X, CheckCircle2, AlertCircle } from "lucide-react";
import FeedbackControls from "./FeedbackControls";

interface Props {
  leadId: string;
  onClose: () => void;
}

export default function LeadDetailPanel({ leadId, onClose }: Props) {
  const { data: intel, isLoading: isLoadingIntel, isError: isErrorIntel } = useQuery({
    queryKey: ["lead-intel", leadId],
    queryFn: () => fetchLeadIntelligence(leadId),
  });

  const { data: feedback, isLoading: isLoadingFeedback } = useQuery({
    queryKey: ["lead-feedback", leadId],
    queryFn: () => fetchLeadFeedback(leadId),
  });

  if (isLoadingIntel) {
    return (
      <div className="p-8 space-y-6">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (isErrorIntel || !intel) {
    return <div className="p-8 text-flag-600">Failed to load lead intelligence.</div>;
  }

  const { explanation, recommendation } = intel;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b border-line-200">
        <h2 className="font-mono text-sm font-medium">Lead: {leadId.substring(0, 8)}...</h2>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
          <X className="w-4 h-4" />
        </Button>
      </div>

      <div className="p-6 flex-1 overflow-y-auto">
        {/* Verdict */}
        <div className="mb-10">
          <div className="text-xs text-ink-900/60 uppercase tracking-widest mb-2 font-medium">Verdict</div>
          <div className="flex items-baseline gap-4 mb-2">
            <span className={`text-5xl font-mono tracking-tight ${intel.lead_score >= 75 ? 'text-signal-600' : intel.lead_score <= 25 ? 'text-flag-600' : ''}`}>
              {intel.lead_score.toFixed(1)}
            </span>
            <span className="text-ink-900/60 font-mono">{(intel.conversion_probability * 100).toFixed(1)}% prob</span>
          </div>
          
          <div className="mt-4 p-3 bg-white border border-line-200 rounded-sm flex items-start gap-3">
            <div className="mt-0.5">
              <div className="w-2 h-2 rounded-full bg-focus-500" />
            </div>
            <div>
              <div className="text-sm font-medium mb-1">Recommend: <span className="uppercase text-focus-500 font-mono tracking-wider">{recommendation.recommended_action}</span></div>
              <p className="text-xs text-ink-900/70">{recommendation.rationale}</p>
            </div>
          </div>
        </div>

        {/* SHAP Explanation */}
        <div className="mb-10">
          <div className="text-xs text-ink-900/60 uppercase tracking-widest mb-4 font-medium">Key Factors</div>
          <p className="text-sm mb-6 leading-relaxed">{explanation.explanation_text}</p>
          
          <div className="space-y-4">
            <div className="grid grid-cols-[1fr_2px_1fr] gap-4">
              {/* Left Side: Negative */}
              <div className="space-y-3 text-right">
                {explanation.negative_factors.map(f => (
                  <div key={f.feature} className="flex justify-end items-center gap-2">
                    <span className="text-xs text-ink-900/70">{f.display_name}</span>
                    <div className="h-4 bg-flag-600/20 border border-flag-600/40 rounded-sm" style={{ width: `${Math.min(Math.abs(f.impact) * 100, 100)}%`, minWidth: '4px' }} />
                  </div>
                ))}
              </div>
              
              {/* Axis */}
              <div className="bg-line-200 h-full w-[1px] mx-auto" />
              
              {/* Right Side: Positive */}
              <div className="space-y-3">
                {explanation.positive_factors.map(f => (
                  <div key={f.feature} className="flex items-center gap-2">
                    <div className="h-4 bg-signal-600/20 border border-signal-600/40 rounded-sm" style={{ width: `${Math.min(f.impact * 100, 100)}%`, minWidth: '4px' }} />
                    <span className="text-xs text-ink-900/70">{f.display_name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Feedback History */}
        {!isLoadingFeedback && feedback && feedback.length > 0 && (
          <div className="mb-6">
            <div className="text-xs text-ink-900/60 uppercase tracking-widest mb-3 font-medium">Feedback History</div>
            <div className="space-y-3 border-l border-line-200 ml-2 pl-4 py-1">
              {feedback.map(fb => (
                <div key={fb.id} className="text-xs relative">
                  <div className={`absolute -left-[21px] top-0 w-2 h-2 rounded-full ${fb.override_action ? 'bg-flag-600' : 'bg-signal-600'}`} />
                  <div className="text-ink-900/50 mb-1 font-mono">{new Date(fb.timestamp).toLocaleString()}</div>
                  {fb.override_action ? (
                    <div>
                      <span className="font-medium">Overrode</span> {fb.original_action} with {fb.override_action}
                      <p className="mt-1 text-ink-900/70 italic">"{fb.reason}"</p>
                    </div>
                  ) : (
                    <div>
                      <span className="font-medium">Accepted</span> {fb.original_action}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <FeedbackControls leadId={leadId} originalAction={recommendation.recommended_action} />
      </div>
    </div>
  );
}
