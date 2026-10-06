"use client";

import { useState } from "react";
import RankedLeadsTable from "@/components/dashboard/RankedLeadsTable";
import LeadDetailPanel from "@/components/dashboard/LeadDetailPanel";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ArrowDownUp } from "lucide-react";

export default function LeadsPage() {
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  
  // Local filtering and sorting state
  const [filterAction, setFilterAction] = useState<string>("ALL");
  const [sortField, setSortField] = useState<'score' | 'probability' | 'rank'>('rank');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const toggleSortDirection = () => {
    setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
  };

  return (
    <div className="flex h-full gap-8">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 space-y-4">
        
        {/* Controls */}
        <div className="flex items-center justify-between bg-white p-4 border border-line-200 rounded-md">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-ink-900/70">Action:</span>
              <Select value={filterAction} onValueChange={(val) => setFilterAction(val || "ALL")}>
                <SelectTrigger className="w-[140px] h-8 text-sm">
                  <SelectValue placeholder="All Actions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Actions</SelectItem>
                  <SelectItem value="CALL">Call</SelectItem>
                  <SelectItem value="EMAIL">Email</SelectItem>
                  <SelectItem value="DEMO">Demo</SelectItem>
                  <SelectItem value="NURTURE">Nurture</SelectItem>
                  <SelectItem value="REVIEW">Review</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-ink-900/70">Sort By:</span>
              <Select value={sortField} onValueChange={(val) => setSortField(val as 'score' | 'probability' | 'rank')}>
                <SelectTrigger className="w-[140px] h-8 text-sm">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="rank">Backend Rank</SelectItem>
                  <SelectItem value="score">Lead Score</SelectItem>
                  <SelectItem value="probability">Conv. Prob.</SelectItem>
                </SelectContent>
              </Select>
              
              <Button 
                variant="outline" 
                size="icon" 
                className="h-8 w-8"
                onClick={toggleSortDirection}
                title={`Sort ${sortDirection === 'asc' ? 'Ascending' : 'Descending'}`}
              >
                <ArrowDownUp className="w-4 h-4 text-ink-900/60" />
              </Button>
            </div>
          </div>
          
          <div className="text-xs text-ink-900/50">
            {sortField !== 'rank' && "Using Local Sorting"}
          </div>
        </div>

        {/* Ranked Leads Table */}
        <div className="flex-1">
          <RankedLeadsTable 
            selectedLeadId={selectedLeadId}
            onSelectLead={setSelectedLeadId}
            filterAction={filterAction}
            sortField={sortField}
            sortDirection={sortDirection}
            // limit={50} // Can leave limit undefined for leads page to show all fetched
          />
        </div>
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
