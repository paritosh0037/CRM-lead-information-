import { RankedLeadItem } from "@/lib/types";

interface LeadContextCardProps {
  leadInfo: RankedLeadItem | null;
}

export default function LeadContextCard({ leadInfo }: LeadContextCardProps) {
  if (!leadInfo) {
    return (
      <div className="bg-white p-6 border border-line-200 rounded-md shadow-sm h-full">
        <h3 className="text-xs text-ink-900/60 uppercase tracking-widest mb-4 font-medium">Account Info</h3>
        <div className="text-sm text-ink-900/50">Context information unavailable.</div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 border border-line-200 rounded-md shadow-sm h-full">
      <h3 className="text-xs text-ink-900/60 uppercase tracking-widest mb-4 font-medium">Account Info</h3>
      
      <div className="space-y-4">
        {leadInfo.company_size && (
          <div>
            <div className="text-xs text-ink-900/50 mb-1">Company Size</div>
            <div className="text-sm font-medium">{leadInfo.company_size}</div>
          </div>
        )}
        
        {leadInfo.industry && (
          <div>
            <div className="text-xs text-ink-900/50 mb-1">Industry</div>
            <div className="text-sm font-medium">{leadInfo.industry}</div>
          </div>
        )}
        
        {leadInfo.opportunity_stage && (
          <div>
            <div className="text-xs text-ink-900/50 mb-1">Opportunity Stage</div>
            <div className="text-sm font-medium">{leadInfo.opportunity_stage}</div>
          </div>
        )}
        
        {leadInfo.deal_value !== undefined && leadInfo.deal_value !== null && (
          <div>
            <div className="text-xs text-ink-900/50 mb-1">Deal Value</div>
            <div className="text-sm font-medium font-mono">${leadInfo.deal_value.toLocaleString()}</div>
          </div>
        )}
      </div>
    </div>
  );
}
