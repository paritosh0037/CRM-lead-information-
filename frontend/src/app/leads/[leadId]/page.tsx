import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import LeadIntelligenceView from "@/components/leads/LeadIntelligenceView";

interface Props {
  params: Promise<{ leadId: string }>;
}

export default async function LeadPage({ params }: Props) {
  const { leadId } = await params;
  
  return (
    <div className="max-w-5xl mx-auto w-full space-y-4">
      <Link 
        href="/leads" 
        className="inline-flex items-center gap-2 text-sm text-ink-900/60 hover:text-ink-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Leads
      </Link>
      
      <LeadIntelligenceView leadId={leadId} />
    </div>
  );
}
