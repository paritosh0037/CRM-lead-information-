"use client";

import { useState } from "react";
import AnalyticsSummary from "@/components/dashboard/AnalyticsSummary";
import RankedLeadsTable from "@/components/dashboard/RankedLeadsTable";
import LeadDetailPanel from "@/components/dashboard/LeadDetailPanel";

export default function DashboardPage() {
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);

  return (
    <div className="flex h-full gap-8">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 space-y-8">
        {/* Analytics Strip */}
        <section>
          <h2 className="text-sm text-ink-900/60 mb-3 font-medium uppercase tracking-wider">Overview</h2>
          <AnalyticsSummary />
        </section>

        {/* Ranked Leads Table */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm text-ink-900/60 font-medium uppercase tracking-wider">Top Priority Leads</h2>
          </div>
          <RankedLeadsTable 
            selectedLeadId={selectedLeadId}
            onSelectLead={setSelectedLeadId}
            limit={10} 
          />
        </section>
      </div>

      {/* Side Panel for Lead Details */}
      {selectedLeadId && (
        <div className="w-[450px] flex-shrink-0 bg-white border border-line-200 rounded-md shadow-sm h-[calc(100vh-8rem)] sticky top-0 overflow-hidden">
          <LeadDetailPanel 
            leadId={selectedLeadId} 
            onClose={() => setSelectedLeadId(null)} 
          />
        </div>
      )}
    </div>
  );
}
