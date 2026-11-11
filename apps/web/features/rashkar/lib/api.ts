import { apiFetch } from "@/lib/api/client";
import type { Farm } from "@/lib/api/types";
import type {
  CropHeatAssessmentRequest,
  CropHeatAssessmentResponse,
  CropHeatHistoryItem,
  DiscoveredOpportunity,
  EnterpriseFinancialAnalysis,
  FarmerResourceProfile,
  HistoricalYieldBaseline,
  OpportunityCatalogItem,
  OpportunityComparisonItem,
  RashkarCanonicalCropItem,
  RashkarCropCycle,
  RashkarCropCycleCreate,
  RashkarCropCycleUpdate,
  RashkarOverviewResponse,
  SavedIncomePlan,
  ScenarioCalculateRequest,
  WorkerHeatAssessmentRequest,
  WorkerHeatAssessmentResponse,
  WorkerHeatHistoryItem,
  YieldHistoryItem,
  YieldRiskResponse,
} from "../types";

export const rashkarApi = {
  // ── Context, Canonical Crops & Crop Cycles ──────────────────────────────────
  listCrops: (includeStages = false) =>
    apiFetch<RashkarCanonicalCropItem[]>(
      `/api/v1/rashkar/crops?include_stages=${includeStages ? "true" : "false"}`,
    ),

  getOverview: (farmId: string) =>
    apiFetch<RashkarOverviewResponse>(`/api/v1/rashkar/farms/${farmId}/overview`),

  listCropCycles: (farmId: string) =>
    apiFetch<RashkarCropCycle[]>(`/api/v1/rashkar/farms/${farmId}/crop-cycles`),

  upsertActiveCropCycle: (farmId: string, payload: RashkarCropCycleCreate) =>
    apiFetch<RashkarCropCycle>(`/api/v1/rashkar/farms/${farmId}/crop-cycle`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateCropCycle: (farmId: string, cycleId: string, payload: RashkarCropCycleUpdate) =>
    apiFetch<RashkarCropCycle>(`/api/v1/rashkar/farms/${farmId}/crop-cycle/${cycleId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  confirmCropStage: (farmId: string, stageCode: string, cycleId?: string | null) =>
    apiFetch<RashkarCropCycle>(`/api/v1/rashkar/farms/${farmId}/crop-cycle/confirm-stage`, {
      method: "POST",
      body: JSON.stringify({
        stage_code: stageCode,
        ...(cycleId ? { cycle_id: cycleId } : {}),
      }),
    }),

  // ── Worker Heat & WBGT ──────────────────────────────────────────────────────
  assessWorkerHeat: (payload: WorkerHeatAssessmentRequest) =>
    apiFetch<WorkerHeatAssessmentResponse>("/api/v1/rashkar/worker-heat/assess", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getWorkerHeatHistory: (farmId: string, limit = 20) =>
    apiFetch<WorkerHeatHistoryItem[]>(
      `/api/v1/rashkar/worker-heat/farms/${farmId}/history?limit=${limit}`,
    ),

  // ── Crop Heat Stress ────────────────────────────────────────────────────────
  assessCropHeat: (payload: CropHeatAssessmentRequest) =>
    apiFetch<CropHeatAssessmentResponse>("/api/v1/rashkar/crop-heat/assess", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getCropHeatHistory: (farmId: string, limit = 20) =>
    apiFetch<CropHeatHistoryItem[]>(
      `/api/v1/rashkar/crop-heat/farms/${farmId}/history?limit=${limit}`,
    ),

  // ── Yield Intelligence & DES APY Baseline ───────────────────────────────────
  getYieldAssessment: (
    farmId: string,
    options?: { cropCode?: string | null; farmerConfirmedStage?: string | null },
  ) => {
    const params = new URLSearchParams();
    if (options?.cropCode) params.set("crop_code", options.cropCode);
    if (options?.farmerConfirmedStage) {
      params.set("farmer_confirmed_stage", options.farmerConfirmedStage);
    }
    const qs = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<YieldRiskResponse>(`/api/v1/rashkar/yield/farms/${farmId}/assessment${qs}`);
  },

  getYieldHistory: (farmId: string, limit = 20) =>
    apiFetch<YieldHistoryItem[]>(`/api/v1/rashkar/yield/farms/${farmId}/history?limit=${limit}`),

  getYieldBaseline: (district: string, cropCode: string) => {
    const params = new URLSearchParams({
      district,
      crop_code: cropCode,
    });
    return apiFetch<HistoricalYieldBaseline>(`/api/v1/rashkar/yield/baseline?${params.toString()}`);
  },

  // ── Extra Income ("Earn More") ──────────────────────────────────────────────
  listIncomeOpportunities: (category?: string) => {
    const qs = category && category !== "all" ? `?category=${encodeURIComponent(category)}` : "";
    return apiFetch<OpportunityCatalogItem[]>(`/api/v1/rashkar/income/opportunities${qs}`);
  },

  getIncomeProfile: (farmId: string) =>
    apiFetch<FarmerResourceProfile>(`/api/v1/rashkar/income/farms/${farmId}/profile`),

  updateIncomeProfile: (farmId: string, profile: FarmerResourceProfile) =>
    apiFetch<FarmerResourceProfile>(`/api/v1/rashkar/income/farms/${farmId}/profile`, {
      method: "PUT",
      body: JSON.stringify(profile),
    }),

  discoverOpportunities: (farmId: string, profileOverride?: FarmerResourceProfile | null) =>
    apiFetch<DiscoveredOpportunity[]>(`/api/v1/rashkar/income/farms/${farmId}/discover`, {
      method: "POST",
      body: profileOverride ? JSON.stringify(profileOverride) : undefined,
    }),

  calculateFarmScenario: (farmId: string, payload: ScenarioCalculateRequest) =>
    apiFetch<EnterpriseFinancialAnalysis>(
      `/api/v1/rashkar/income/farms/${farmId}/calculate-scenario`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),

  compareOpportunities: (opportunityIds: string[], customBudgetInr = 60000) =>
    apiFetch<OpportunityComparisonItem[]>("/api/v1/rashkar/income/compare-opportunities", {
      method: "POST",
      body: JSON.stringify({
        opportunity_ids: opportunityIds,
        custom_budget_inr: customBudgetInr,
      }),
    }),

  listSavedPlans: (farmId: string) =>
    apiFetch<SavedIncomePlan[]>(`/api/v1/rashkar/income/farms/${farmId}/plans`),

  saveIncomePlan: (
    farmId: string,
    payload: { opportunity_id: string; chosen_budget_inr: number; notes?: string | null },
  ) =>
    apiFetch<SavedIncomePlan>(`/api/v1/rashkar/income/farms/${farmId}/plans`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteSavedPlan: (farmId: string, planId: string) =>
    apiFetch<{ status: string; plan_id: string; farm_id: string }>(
      `/api/v1/rashkar/income/farms/${farmId}/plans/${planId}`,
      {
        method: "DELETE",
      },
    ),
};

/**
 * Extracts valid Indian-bounds coordinates from a canonical CropNet Farm object,
 * returning undefined for any unpopulated or out-of-bounds value so backend farm_id lookup handles it.
 */
export function resolveValidFarmCoordinates(
  farm: Farm | null | undefined,
): { latitude?: number; longitude?: number } {
  if (!farm) return {};
  const lat = farm.centroid_latitude ?? farm.latitude;
  const lon = farm.centroid_longitude ?? farm.longitude;
  if (
    typeof lat === "number" &&
    typeof lon === "number" &&
    Number.isFinite(lat) &&
    Number.isFinite(lon) &&
    lat >= 8.0 &&
    lat <= 37.0 &&
    lon >= 68.0 &&
    lon <= 98.0
  ) {
    return { latitude: lat, longitude: lon };
  }
  return {};
}
