import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "../api/client";

export interface TierQuota {
  tier: "standard" | "upgraded";
  used: number;
  limit: number;
  remaining: number;
  reset_date: string;
  bypassed: boolean;
}

export interface QuotaStatus {
  tiers: TierQuota[];
  maximum_sources_per_run: number;
  maximum_gap_research_loops: number;
  can_start_research: boolean;
}

/** Load the signed-in user's daily research allowance. */
export function useQuotaStatus(): ReturnType<typeof useQuery<QuotaStatus>> {
  return useQuery({
    queryKey: ["quota-status"],
    queryFn: () => apiRequest<QuotaStatus>("/quotas/me"),
  });
}

