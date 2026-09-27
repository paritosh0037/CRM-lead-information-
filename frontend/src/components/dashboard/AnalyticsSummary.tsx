"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAnalytics } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function AnalyticsSummary() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["analytics"],
    queryFn: fetchAnalytics,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return <div className="text-flag-600 text-sm">Failed to load analytics.</div>;
  }

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="grid grid-cols-4 gap-4">
      <Card className="shadow-none border-line-200">
        <CardContent className="p-4 flex flex-col justify-center h-full">
          <div className="text-xs text-ink-900/60 mb-1">Total Leads</div>
          <div className="text-2xl font-mono">{data.total_leads.toLocaleString()}</div>
        </CardContent>
      </Card>
      
      <Card className="shadow-none border-line-200">
        <CardContent className="p-4 flex flex-col justify-center h-full">
          <div className="text-xs text-ink-900/60 mb-1">High Priority</div>
          <div className="text-2xl font-mono text-signal-600">{data.high_priority_leads.toLocaleString()}</div>
        </CardContent>
      </Card>
      
      <Card className="shadow-none border-line-200">
        <CardContent className="p-4 flex flex-col justify-center h-full">
          <div className="text-xs text-ink-900/60 mb-1">Avg Score</div>
          <div className="text-2xl font-mono">{data.average_lead_score.toFixed(1)}</div>
        </CardContent>
      </Card>

      <Card className="shadow-none border-line-200">
        <CardContent className="p-4 flex flex-col justify-center h-full">
          <div className="text-xs text-ink-900/60 mb-1">Pipeline Value</div>
          <div className="text-2xl font-mono">{formatCurrency(data.pipeline_value)}</div>
        </CardContent>
      </Card>
    </div>
  );
}
