"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchLeadInteractions } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

interface InteractionTimelineProps {
  leadId: string;
}

export default function InteractionTimeline({ leadId }: InteractionTimelineProps) {
  const { data: interactions, isLoading, isError } = useQuery({
    queryKey: ["lead-interactions", leadId],
    queryFn: () => fetchLeadInteractions(leadId),
  });

  return (
    <div className="bg-white p-6 border border-line-200 rounded-md shadow-sm h-full">
      <h3 className="text-xs text-ink-900/60 uppercase tracking-widest mb-4 font-medium">Interaction Timeline</h3>
      
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex gap-4">
              <Skeleton className="w-2 h-2 rounded-full mt-2" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          ))}
        </div>
      ) : isError || !interactions || interactions.length === 0 ? (
        <div className="py-12 flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 rounded-full bg-line-50 flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-ink-900/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-sm font-medium text-ink-900/70 mb-1">
            {isError ? "Failed to load interactions" : "No interaction history available."}
          </p>
          <p className="text-xs text-ink-900/40">This lead has not recorded any recent interactions.</p>
        </div>
      ) : (
        <div className="relative border-l border-line-200 ml-3 pl-6 space-y-6">
          {interactions.map((interaction, i) => (
            <div key={interaction.id || i} className="relative">
              <div className="absolute -left-[29px] top-1.5 w-2 h-2 rounded-full bg-ink-900/20 border-2 border-white ring-4 ring-white" />
              <div className="text-sm font-medium text-ink-900">
                {interaction.interaction_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </div>
              <div className="text-xs text-ink-900/60 font-mono mt-1">
                {new Date(interaction.timestamp).toLocaleString()}
                {interaction.duration ? ` • ${interaction.duration}s` : ""}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
