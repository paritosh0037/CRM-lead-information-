interface LeadScoreCardProps {
  score: number;
  probability: number;
}

export default function LeadScoreCard({ score, probability }: LeadScoreCardProps) {
  const isHigh = score >= 75;
  const isLow = score <= 25;
  
  return (
    <div className="bg-white p-6 border border-line-200 rounded-md shadow-sm">
      <h3 className="text-xs text-ink-900/60 uppercase tracking-widest mb-4 font-medium">Lead Score</h3>
      
      <div className="flex items-baseline gap-4 mb-4">
        <div className={`text-6xl font-mono tracking-tight ${isHigh ? 'text-signal-600' : isLow ? 'text-flag-600' : 'text-ink-900'}`}>
          {score.toFixed(1)}
        </div>
        <div className="text-2xl text-ink-900/40 font-light">/ 100</div>
      </div>
      
      <div className="pt-4 border-t border-line-100 flex items-center justify-between">
        <span className="text-sm font-medium text-ink-900/70">Conversion Probability</span>
        <span className="font-mono font-medium text-lg">{(probability * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}
