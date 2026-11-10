import type {
  Farm,
  FarmCreate,
  FarmUpdate,
  CurrentWeather,
  WeatherForecast,
  ClimateSummary,
  SoilProfile,
  SoilTestReport,
  FarmHealthSnapshot,
  WaterSource,
  WaterEvaluation,
  SatelliteObservation,
  CropDoctorStatus,
  CropDoctorPrediction,
  HeatRiskCropsResponse,
  CropHeatRequest,
  CropHeatResponse,
  WorkerHeatRequest,
  WorkerHeatResponse,
  FarmHeatRiskRequest,
  FarmHeatRiskResponse,
  Crop,
  CropRequirement,
  GovernmentScheme,
  SchemeFilters,
  SchemeAdminStatus,
  IncomeOpportunity,
  CropDecisionResponse,
  FarmEvaluationResponse,
  AgriculturalExplanationResponse,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export const DEFAULT_DEV_USER_ID = "00000000-0000-0000-0000-000000000001";

/**
 * Returns authentication headers based on active session token or development bypass.
 */
export function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};

  if (typeof window !== "undefined") {
    // 1. Check for live Supabase JWT token in localStorage/cookie
    const token = localStorage.getItem("cropnet_access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
      return headers;
    }

    // 2. Dev mode bypass
    const devUserId = localStorage.getItem("cropnet_dev_user_id") || DEFAULT_DEV_USER_ID;
    headers["X-Dev-User-Id"] = devUserId;
  } else {
    // Server-side fallback for local development
    headers["X-Dev-User-Id"] = DEFAULT_DEV_USER_ID;
  }

  return headers;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const authHeaders = getAuthHeaders();
  const url = `${API_BASE_URL.replace(/\/$/, "")}${path}`;

  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
      ...authHeaders,
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = `API request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        if (typeof errJson.detail === "string") {
          errorDetail = errJson.detail;
        } else if (Array.isArray(errJson.detail)) {
          errorDetail = errJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ");
        }
      }
    } catch {
      // Ignore JSON parsing failure for non-JSON errors
    }
    const err = new Error(errorDetail) as Error & { status: number };
    err.status = response.status;
    throw err;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const authHeaders = getAuthHeaders();
  // Do NOT set Content-Type header so browser sets multipart boundary automatically
  delete (authHeaders as any)["Content-Type"];

  const url = `${API_BASE_URL.replace(/\/$/, "")}${path}`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      ...authHeaders,
    },
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = `Upload failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // fallback
    }
    const err = new Error(errorDetail) as Error & { status: number };
    err.status = response.status;
    throw err;
  }

  return response.json() as Promise<T>;
}

// ── Specific API Client Modules ──────────────────────────────────────────────

export const farmsApi = {
  list: () => apiFetch<Farm[]>("/api/v1/farms"),
  get: (id: string) => apiFetch<Farm>(`/api/v1/farms/${id}`),
  create: (data: FarmCreate) =>
    apiFetch<Farm>("/api/v1/farms", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: string, data: FarmUpdate) =>
    apiFetch<Farm>(`/api/v1/farms/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    apiFetch<void>(`/api/v1/farms/${id}`, {
      method: "DELETE",
    }),
};

export const weatherApi = {
  getCurrent: (farmId: string) => apiFetch<CurrentWeather>(`/api/v1/farms/${farmId}/weather/current`),
  getForecast: (farmId: string) => apiFetch<WeatherForecast>(`/api/v1/farms/${farmId}/weather/forecast`),
  getClimateSummary: (farmId: string) => apiFetch<ClimateSummary>(`/api/v1/farms/${farmId}/weather/climate-summary`),
};

export const soilApi = {
  getProfile: (farmId: string) => apiFetch<SoilProfile>(`/api/v1/farms/${farmId}/soil`),
  analyse: (farmId: string, depth = "0-5cm") =>
    apiFetch<SoilProfile>(`/api/v1/farms/${farmId}/soil/analyse?depth=${encodeURIComponent(depth)}`, {
      method: "POST",
    }),
  listReports: (farmId: string) => apiFetch<SoilTestReport[]>(`/api/v1/farms/${farmId}/soil-reports`),
  getReport: (farmId: string, reportId: string) =>
    apiFetch<SoilTestReport>(`/api/v1/farms/${farmId}/soil-reports/${reportId}`),
  uploadReport: (farmId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiUpload<SoilTestReport>(`/api/v1/farms/${farmId}/soil-reports/upload`, formData);
  },
  confirmReport: (farmId: string, reportId: string, confirmedData?: any) =>
    apiFetch<SoilTestReport>(`/api/v1/farms/${farmId}/soil-reports/${reportId}/confirm`, {
      method: "POST",
      body: JSON.stringify(confirmedData || {}),
    }),
  deleteReport: (farmId: string, reportId: string) =>
    apiFetch<void>(`/api/v1/farms/${farmId}/soil-reports/${reportId}`, {
      method: "DELETE",
    }),
};

export const farmHealthApi = {
  getSnapshot: (farmId: string, forceRefresh = false, targetSeason?: string) => {
    const params = new URLSearchParams();
    if (forceRefresh) params.set("force_refresh", "true");
    if (targetSeason) params.set("target_season", targetSeason);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<FarmHealthSnapshot>(`/api/v1/farms/${farmId}/health-snapshot${qs}`);
  },
  invalidate: (farmId: string) =>
    apiFetch<{ message: string }>(`/api/v1/farms/${farmId}/health-snapshot/invalidate`, {
      method: "POST",
    }),
};

export const waterApi = {
  listSources: (farmId: string) => apiFetch<WaterSource[]>(`/api/v1/farms/${farmId}/water/sources`),
  createSource: (farmId: string, data: Partial<WaterSource>) =>
    apiFetch<WaterSource>(`/api/v1/farms/${farmId}/water/sources`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getEvaluation: (farmId: string) => apiFetch<WaterEvaluation>(`/api/v1/farms/${farmId}/water/evaluation`),
};

export const satelliteApi = {
  sync: (farmId: string) =>
    apiFetch<SatelliteObservation>(`/api/v1/farms/${farmId}/satellite/sync`, {
      method: "POST",
    }),
  getLatest: (farmId: string) => apiFetch<SatelliteObservation>(`/api/v1/farms/${farmId}/satellite/latest`),
  getTimeseries: (farmId: string) => apiFetch<any>(`/api/v1/farms/${farmId}/satellite/timeseries`),
};

export const cropsApi = {
  list: (category?: string, season?: string) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (season) params.set("season", season);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<Crop[]>(`/api/v1/crops${qs}`);
  },
  get: (id: string) => apiFetch<Crop>(`/api/v1/crops/${id}`),
  getRequirements: (id: string) => apiFetch<CropRequirement>(`/api/v1/crops/${id}/requirements`),
};

export const cropDoctorApi = {
  getStatus: () => apiFetch<CropDoctorStatus>("/api/v1/crop-doctor/status"),
  predict: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiUpload<CropDoctorPrediction>("/api/v1/crop-doctor/predict", formData);
  },
};

export const heatRiskApi = {
  getCrops: () => apiFetch<HeatRiskCropsResponse>("/api/v1/heat-risk/crops"),
  assessCrop: (data: CropHeatRequest) =>
    apiFetch<CropHeatResponse>("/api/v1/heat-risk/crop", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  assessWorker: (data: WorkerHeatRequest) =>
    apiFetch<WorkerHeatResponse>("/api/v1/heat-risk/worker", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  assessFarm: (farmId: string, data?: Partial<FarmHeatRiskRequest>) =>
    apiFetch<FarmHeatRiskResponse>(`/api/v1/heat-risk/farm/${farmId}`, {
      method: "POST",
      body: JSON.stringify(data || { crop_code: "soybean" }),
    }),
};

export const schemesApi = {
  list: (params?: { search?: string; category?: string; government_level?: string; state?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.category) q.set("category", params.category);
    if (params?.government_level) q.set("government_level", params.government_level);
    if (params?.state) q.set("state", params.state);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return apiFetch<GovernmentScheme[]>(`/api/v1/schemes${qs}`);
  },
  getFilters: () => apiFetch<SchemeFilters>("/api/v1/schemes/filters"),
  get: (id: string) => apiFetch<GovernmentScheme>(`/api/v1/schemes/${id}`),
  getAdminStatus: () => apiFetch<SchemeAdminStatus>("/api/v1/schemes/admin/status"),
  create: (data: Partial<GovernmentScheme>) =>
    apiFetch<GovernmentScheme>("/api/v1/schemes", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: string, data: Partial<GovernmentScheme>) =>
    apiFetch<GovernmentScheme>(`/api/v1/schemes/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    apiFetch<void>(`/api/v1/schemes/${id}`, {
      method: "DELETE",
    }),
  seed: () =>
    apiFetch<{ message: string; count: number }>("/api/v1/schemes/seed", {
      method: "POST",
    }),
};

export const incomeApi = {
  listOpportunities: (category?: string, maxBudget?: number) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (maxBudget) params.set("max_budget", maxBudget.toString());
    const qs = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<IncomeOpportunity[]>(`/api/v1/income/opportunities${qs}`);
  },
  getOpportunity: (id: string) => apiFetch<IncomeOpportunity>(`/api/v1/income/opportunities/${id}`),
};

export const advisoryApi = {
  evaluateFarm: (data: any) =>
    apiFetch<FarmEvaluationResponse>("/api/v1/agriculture/evaluate-farm", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getDecision: (decisionId: string) =>
    apiFetch<FarmEvaluationResponse>(`/api/v1/agriculture/decision/${decisionId}`),
  processFollowup: (data: { decision_id: string; answers: Record<string, any> }) =>
    apiFetch<FarmEvaluationResponse>("/api/v1/agriculture/follow-up", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  explainDecision: (data: { decision_id: string; language?: string }) =>
    apiFetch<AgriculturalExplanationResponse>(
      "/api/v1/agriculture/explain-decision",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),
  conversation: (data: {
    decision_id: string;
    message: string;
    language?: string;
    history?: Array<{ role: string; content: string; timestamp?: string }>;
    submitted_answers?: Record<string, any>;
  }) =>
    apiFetch<AgriculturalExplanationResponse>("/api/v1/agriculture/conversation", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
