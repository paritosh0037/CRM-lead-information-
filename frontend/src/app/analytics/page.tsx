"use client";

import AnalyticsSummary from "@/components/dashboard/AnalyticsSummary";

export default function AnalyticsPage() {
  return (
    <div className="flex-1 flex flex-col min-w-0 space-y-8 max-w-5xl mx-auto w-full">
      <div className="bg-white p-8 border border-line-200 rounded-md shadow-sm space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight mb-2">Analytics</h1>
          <p className="text-ink-900/60">
            Overview of CRM lead performance and recommendation distribution. 
            Detailed reporting and deep-dives will be available in a future update.
          </p>
        </div>
        
        <AnalyticsSummary />
      </div>
    </div>
  );
}
