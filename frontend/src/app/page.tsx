"use client";

import { useState } from "react";
import AnalyticsSummary from "@/components/dashboard/AnalyticsSummary";
import RankedLeadsTable from "@/components/dashboard/RankedLeadsTable";
import LeadDetailPanel from "@/components/dashboard/LeadDetailPanel";

export default function DashboardPage() {
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);

  return (
    <div className="flex h-screen overflow-hidden bg-paper-50 text-ink-900">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto border-r border-line-200">
        <header className="px-8 py-6 border-b border-line-200 bg-paper-100 flex items-center justify-between">
          <h1 className="text-xl font-medium tracking-tight">AI Sales Intelligence</h1>
        </header>

        <main className="flex-1 p-8 space-y-8 max-w-[1200px] w-full mx-auto">
          {/* Analytics Strip */}
          <section>
            <h2 className="text-sm text-ink-900/60 mb-3 font-medium uppercase tracking-wider">Overview</h2>
            <AnalyticsSummary />
          </section>

          {/* Ranked Leads Table */}
          <section>
            <h2 className="text-sm text-ink-900/60 mb-3 font-medium uppercase tracking-wider">Prioritized Leads</h2>
            <RankedLeadsTable 
              selectedLeadId={selectedLeadId}
              onSelectLead={setSelectedLeadId} 
            />
          </section>
        </main>
      </div>

      {/* Side Panel for Lead Details */}
      <div className="w-[450px] flex-shrink-0 bg-paper-100 overflow-y-auto">
        {selectedLeadId ? (
          <LeadDetailPanel 
            leadId={selectedLeadId} 
            onClose={() => setSelectedLeadId(null)} 
          />
        ) : (
          <div className="h-full flex items-center justify-center text-ink-900/50 p-8 text-center">
            <p>Select a lead from the prioritized list to view intelligence and recommendations.</p>
          </div>
        )}
      </div>
    </div>
  );
}
