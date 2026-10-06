import { Badge } from "@/components/ui/badge";

interface LeadHeaderProps {
  leadId: string;
}

export default function LeadHeader({ leadId }: LeadHeaderProps) {
  return (
    <div className="flex items-center justify-between pb-4 border-b border-line-200">
      <div>
        <h1 className="text-2xl font-bold tracking-tight mb-1">Lead Details</h1>
        <div className="flex items-center gap-2">
          <span className="text-ink-900/60 text-sm">ID:</span>
          <span className="font-mono text-sm">{leadId}</span>
        </div>
      </div>
      <div>
        <Badge variant="outline" className="text-xs uppercase tracking-wider text-ink-900/60">
          AI Intelligence Active
        </Badge>
      </div>
    </div>
  );
}
