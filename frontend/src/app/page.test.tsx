import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import DashboardPage from "./dashboard/page";
import * as api from "@/lib/api";

// Mock the API module
vi.mock("@/lib/api", () => ({
  fetchAnalytics: vi.fn(),
  fetchRankedLeads: vi.fn(),
  fetchLeadIntelligence: vi.fn(),
  fetchLeadFeedback: vi.fn(),
  acceptRecommendation: vi.fn(),
  overrideRecommendation: vi.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const renderWithProviders = (component: React.ReactNode) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe("DashboardPage", () => {
  it("renders the dashboard layout correctly", async () => {
    vi.mocked(api.fetchAnalytics).mockResolvedValue({
      total_leads: 5000,
      high_priority_leads: 200,
      pipeline_value: 1500000,
      average_lead_score: 65,
      score_distribution: {},
      score_by_opportunity_stage: {},
      action_distribution: {},
    });

    vi.mocked(api.fetchRankedLeads).mockResolvedValue({
      total: 10,
      limit: 50,
      offset: 0,
      leads: [
        {
          lead_id: "lead_123",
          lead_score: 85,
          conversion_probability: 0.85,
          recommended_action: "CALL",
          recommendation_confidence: 0.9,
          company_size: "Mid-Market",
          industry: "Technology",
          opportunity_stage: "New",
        },
      ],
    });

    renderWithProviders(<DashboardPage />);
    
    // Check if overview section title exists
    expect(screen.getByText("Overview")).toBeTruthy();
    
    // Check if analytics loaded
    await waitFor(() => {
      expect(screen.getByText("5,000")).toBeTruthy();
      expect(screen.getByText("200")).toBeTruthy();
    });

    // Check if ranked lead loaded
    await waitFor(() => {
      expect(screen.getByText("Mid-Market • Technology")).toBeTruthy();
      expect(screen.getByText("85.0")).toBeTruthy();
    });
  });
});
