"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchRankedLeads } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface Props {
  selectedLeadId: string | null;
  onSelectLead: (id: string) => void;
  limit?: number;
  filterAction?: string | null;
  sortField?: 'score' | 'probability' | 'rank';
  sortDirection?: 'asc' | 'desc';
}

export default function RankedLeadsTable({ 
  selectedLeadId, 
  onSelectLead, 
  limit,
  filterAction,
  sortField = 'rank',
  sortDirection = 'asc'
}: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["ranked-leads"],
    queryFn: () => fetchRankedLeads(200, 0), // fetch more for local filtering/sorting
  });

  if (isLoading) {
    return (
      <div className="border border-line-200 rounded-md bg-white p-4">
        <Skeleton className="h-8 w-full mb-2" />
        <Skeleton className="h-8 w-full mb-2" />
        <Skeleton className="h-8 w-full mb-2" />
        <Skeleton className="h-8 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return <div className="text-flag-600 text-sm">Failed to load prioritized leads.</div>;
  }

  if (data.leads.length === 0) {
    return (
      <div className="border border-line-200 rounded-md bg-white p-8 text-center text-ink-900/60">
        Run scoring to see ranked leads
      </div>
    );
  }

  // Local filtering and sorting
  let displayLeads = [...data.leads];
  
  if (filterAction && filterAction !== "ALL") {
    displayLeads = displayLeads.filter(l => l.recommended_action === filterAction);
  }
  
  displayLeads.sort((a, b) => {
    let cmp = 0;
    if (sortField === 'score') cmp = a.lead_score - b.lead_score;
    else if (sortField === 'probability') cmp = a.conversion_probability - b.conversion_probability;
    else {
      // Original rank is implicit in the array index of data.leads
      const aIdx = data.leads.findIndex(l => l.lead_id === a.lead_id);
      const bIdx = data.leads.findIndex(l => l.lead_id === b.lead_id);
      cmp = bIdx - aIdx; // Reverse so asc means top rank (index 0) first
    }
    return sortDirection === 'asc' ? cmp : -cmp;
  });

  if (limit) {
    displayLeads = displayLeads.slice(0, limit);
  }

  return (
    <div className="border border-line-200 rounded-md bg-white overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-paper-50 hover:bg-paper-50">
            <TableHead className="w-16">Rank</TableHead>
            <TableHead>Company / Stage</TableHead>
            <TableHead className="text-right">Score</TableHead>
            <TableHead className="text-right">Conv. Prob.</TableHead>
            <TableHead className="w-32 text-right">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayLeads.length === 0 ? (
            <TableRow>
              <TableCell colSpan={5} className="text-center py-8 text-ink-900/50">
                No leads match the current filters.
              </TableCell>
            </TableRow>
          ) : (
            displayLeads.map((lead) => {
              // Calculate actual backend rank regardless of local sort/filter
              const actualRank = data.leads.findIndex(l => l.lead_id === lead.lead_id) + 1;
              return (
                <TableRow 
                  key={lead.lead_id}
                  className={`cursor-pointer transition-colors hover:bg-paper-100 ${selectedLeadId === lead.lead_id ? 'bg-focus-500/10 hover:bg-focus-500/10' : ''}`}
                  onClick={() => onSelectLead(lead.lead_id)}
                >
                  <TableCell className="font-mono text-sm text-ink-900/50">{actualRank}</TableCell>
                  <TableCell>
                    <div className="font-medium">{lead.company_size || "Unknown Size"} • {lead.industry || "Unknown Industry"}</div>
                    <div className="text-xs text-ink-900/60">{lead.opportunity_stage || "New"}</div>
                  </TableCell>
                  <TableCell className="text-right font-mono font-medium">
                    <span className={
                      lead.lead_score >= 75 ? "text-signal-600" :
                      lead.lead_score <= 25 ? "text-flag-600" : ""
                    }>
                      {lead.lead_score.toFixed(1)}
                    </span>
              </TableCell>
              <TableCell className="text-right font-mono text-sm">
                {(lead.conversion_probability * 100).toFixed(1)}%
              </TableCell>
              <TableCell className="text-right">
                <Badge variant="outline" className={`font-mono text-[10px] uppercase tracking-wider ${
                  lead.recommended_action === 'CALL' ? 'border-signal-600 text-signal-600' :
                  lead.recommended_action === 'DEMO' ? 'border-focus-500 text-focus-500' :
                  'border-ink-900/20 text-ink-900'
                }`}>
                  {lead.recommended_action}
                </Badge>
              </TableCell>
            </TableRow>
          );
        })
      )}
      </TableBody>
      </Table>
    </div>
  );
}
