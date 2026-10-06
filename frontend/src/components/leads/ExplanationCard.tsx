import { LeadExplanationResponse, FactorDetail } from "@/lib/types";

interface ExplanationCardProps {
  explanation: LeadExplanationResponse;
  rationale: string;
}

export default function ExplanationCard({ explanation, rationale }: ExplanationCardProps) {
  if (!explanation || (explanation.positive_factors.length === 0 && explanation.negative_factors.length === 0)) {
    return (
      <div className="bg-white p-6 border border-line-200 rounded-md shadow-sm h-full">
        <h3 className="text-xs text-ink-900/60 uppercase tracking-widest mb-4 font-medium">AI Explanation</h3>
        <div className="text-sm text-ink-900/50 py-8 text-center bg-line-50 rounded-sm">
          No explanation factors are currently available for this lead.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 border border-line-200 rounded-md shadow-sm h-full">
      <h3 className="text-xs text-ink-900/60 uppercase tracking-widest mb-4 font-medium">AI Explanation</h3>
      
      <div className="mb-6 p-4 bg-line-50 rounded-md border border-line-100">
        <p className="text-sm font-medium mb-2">Why this lead is prioritized:</p>
        <p className="text-sm text-ink-900/80 leading-relaxed mb-4">{explanation.explanation_text}</p>
        
        <p className="text-sm font-medium mb-2">Why did the system recommend this action?</p>
        <p className="text-sm text-ink-900/80 leading-relaxed">{rationale}</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h4 className="text-sm font-semibold mb-4 text-signal-600 border-b border-line-100 pb-2">Positive Factors</h4>
          <div className="space-y-4 mt-4">
            {explanation.positive_factors.map((f: FactorDetail) => (
              <div key={f.feature} className="flex flex-col gap-1">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">{f.display_name}</span>
                  <span className="font-mono text-xs text-signal-600">+{f.impact.toFixed(2)}</span>
                </div>
                <div className="w-full h-1.5 bg-line-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-signal-600 rounded-full" 
                    style={{ width: `${Math.min(f.impact * 50, 100)}%` }} 
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h4 className="text-sm font-semibold mb-4 text-flag-600 border-b border-line-100 pb-2">Negative Factors</h4>
          <div className="space-y-4 mt-4">
            {explanation.negative_factors.map((f: FactorDetail) => (
              <div key={f.feature} className="flex flex-col gap-1">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">{f.display_name}</span>
                  <span className="font-mono text-xs text-flag-600">{f.impact.toFixed(2)}</span>
                </div>
                <div className="w-full h-1.5 bg-line-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-flag-600 rounded-full" 
                    style={{ width: `${Math.min(Math.abs(f.impact) * 50, 100)}%` }} 
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
