import { Badge } from "@/components/ui/badge";
import FeedbackControls from "../dashboard/FeedbackControls";

interface RecommendationCardProps {
  leadId: string;
  action: string;
  confidence: number;
}

export default function RecommendationCard({ leadId, action, confidence }: RecommendationCardProps) {
  const isHighConfidence = confidence >= 0.7;
  const isMediumConfidence = confidence >= 0.4 && confidence < 0.7;
  
  const actionColors: Record<string, string> = {
    CALL: "border-signal-600 text-signal-600 bg-signal-600/10",
    EMAIL: "border-focus-500 text-focus-500 bg-focus-500/10",
    DEMO: "border-focus-500 text-focus-500 bg-focus-500/10",
    NURTURE: "border-ink-900/40 text-ink-900 bg-line-100",
    REVIEW: "border-flag-600 text-flag-600 bg-flag-600/10"
  };

  const confidenceLabel = isHighConfidence ? "High" : isMediumConfidence ? "Medium" : "Low";

  return (
    <div className="bg-white p-6 border border-line-200 rounded-md shadow-sm h-full flex flex-col justify-between">
      <div>
        <h3 className="text-xs text-ink-900/60 uppercase tracking-widest mb-4 font-medium">Recommended Action</h3>
        
        <div className="mb-4">
          <Badge variant="outline" className={`text-lg py-1.5 px-3 font-mono tracking-wider ${actionColors[action] || "border-ink-900/40 text-ink-900"}`}>
            {action}
          </Badge>
        </div>
      </div>
      
      <div>
        <div className="pt-4 border-t border-line-100 flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-ink-900/70">Confidence</span>
          <span className="font-medium text-sm">{confidenceLabel}</span>
        </div>
        <FeedbackControls leadId={leadId} originalAction={action} />
      </div>
    </div>
  );
}
