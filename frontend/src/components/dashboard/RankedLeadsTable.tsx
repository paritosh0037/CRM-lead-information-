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
}

export default function RankedLeadsTable({ selectedLeadId, onSelectLead }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["ranked-leads"],
    queryFn: () => fetchRankedLeads(50, 0),
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
          {data.leads.map((lead, idx) => (
            <TableRow 
              key={lead.lead_id}
              className={`cursor-pointer transition-colors hover:bg-paper-100 ${selectedLeadId === lead.lead_id ? 'bg-focus-500/10 hover:bg-focus-500/10' : ''}`}
              onClick={() => onSelectLead(lead.lead_id)}
            >
              <TableCell className="font-mono text-sm text-ink-900/50">{idx + 1}</TableCell>
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
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
