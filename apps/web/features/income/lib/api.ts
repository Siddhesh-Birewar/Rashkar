import { apiFetch } from "@/lib/api/client";
import type {
  DetailedOpportunity,
  FarmResourceProfile,
  FinancialSimulation,
  OpportunityCategory,
  OpportunityComparison,
  SavedPlan,
} from "../types";

export const incomeApi = {
  getCategories: () =>
    apiFetch<OpportunityCategory[]>("/api/v1/income/categories"),

  getCatalog: (params?: {
    category?: string;
    max_budget?: number;
    min_land?: number;
    water?: string;
    search?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.category && params.category !== "all") q.set("category", params.category);
    if (params?.max_budget !== undefined) q.set("max_budget", params.max_budget.toString());
    if (params?.min_land !== undefined) q.set("min_land", params.min_land.toString());
    if (params?.water && params.water !== "all") q.set("water", params.water);
    if (params?.search) q.set("search", params.search);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return apiFetch<DetailedOpportunity[]>(`/api/v1/income/catalog${qs}`);
  },

  getDetails: (opportunityId: string) =>
    apiFetch<DetailedOpportunity>(`/api/v1/income/details/${opportunityId}`),

  getFarmProfile: (farmId: string) =>
    apiFetch<FarmResourceProfile>(`/api/v1/income/farms/${farmId}/profile`),

  updateFarmProfile: (farmId: string, profile: Partial<FarmResourceProfile>) =>
    apiFetch<{ status: string; message: string }>(`/api/v1/income/farms/${farmId}/profile`, {
      method: "POST",
      body: JSON.stringify(profile),
    }),

  matchOpportunities: (farmId: string, overrides?: Partial<FarmResourceProfile>) =>
    apiFetch<DetailedOpportunity[]>(`/api/v1/income/farms/${farmId}/match`, {
      method: "POST",
      body: JSON.stringify(overrides || {}),
    }),

  simulateScenario: (payload: {
    opportunity_id: string;
    allocated_scale: number;
    custom_setup_investment_inr?: number;
    custom_annual_opex_inr?: number;
    custom_yield?: number;
    custom_sale_price?: number;
    scenario_mode?: "LOW" | "BASE" | "HIGH";
  }) =>
    apiFetch<FinancialSimulation>("/api/v1/income/simulate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  compareOpportunities: (payload: {
    opportunity_ids: string[];
    allocated_acres?: number;
    available_budget_inr?: number;
  }) =>
    apiFetch<OpportunityComparison[]>("/api/v1/income/compare", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getSavedPlans: (farmId: string) =>
    apiFetch<SavedPlan[]>(`/api/v1/income/farms/${farmId}/plans`),

  savePlan: (
    farmId: string,
    payload: {
      opportunity_id: string;
      allocated_scale: number;
      scale_unit: string;
      custom_budget_inr: number;
      projected_operating_surplus_inr: number;
      scenario_mode?: string;
      notes?: string;
    },
  ) =>
    apiFetch<{ status: string; plan_id: string; message: string }>(
      `/api/v1/income/farms/${farmId}/plans`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),

  deletePlan: (farmId: string, planId: string) =>
    apiFetch<{ status: string; message: string }>(
      `/api/v1/income/farms/${farmId}/plans/${planId}`,
      {
        method: "DELETE",
      },
    ),
};
