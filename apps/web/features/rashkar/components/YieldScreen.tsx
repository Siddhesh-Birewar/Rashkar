"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  CloudOff,
  History,
  Info,
  Layers,
  LoaderCircle,
  Lock,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  Sprout,
} from "lucide-react";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { SectionHeader } from "@/components/section-header";
import { rashkarApi } from "../lib/api";
import { formatCropLabel, formatNumber, formatTokenLabel, getRiskTone } from "../lib/format";
import type {
  HistoricalYieldBaseline,
  RashkarCanonicalCropItem,
  YieldHistoryItem,
  YieldRiskResponse,
} from "../types";
import { MoreDetailsPanel } from "./MoreDetailsPanel";
import { RashkarShell, useRashkarShell } from "./RashkarShell";

const RISK_DIMENSION_LABELS: Record<string, string> = {
  weather_dry_spell: "Dry Spell & Moisture Deficit",
  excess_rainfall_waterlogging: "Excess Rainfall & Waterlogging",
  soil_constraint: "Soil Constraints",
  crop_heat_stress: "Crop Heat Stress",
  pest_disease_watch: "Seasonal Weather Anomaly & Pest Watch",
};

const MAHARASHTRA_DISTRICTS = [
  "Ahmednagar",
  "Akola",
  "Amravati",
  "Aurangabad",
  "Beed",
  "Buldhana",
  "Jalgaon",
  "Jalna",
  "Kolhapur",
  "Latur",
  "Nagpur",
  "Nanded",
  "Nashik",
  "Osmanabad",
  "Parbhani",
  "Pune",
  "Sangli",
  "Satara",
  "Solapur",
  "Wardha",
  "Washim",
  "Yavatmal",
];

function BaselineMetricsGrid({ baseline }: { baseline: HistoricalYieldBaseline }) {
  const isStatewideFallback = String(baseline.geographical_unit || "")
    .toLowerCase()
    .startsWith("statewide");
  const hasStats = baseline.historical_mean_t_ha != null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={isStatewideFallback ? "orange" : "green"}>
          {isStatewideFallback
            ? "Statewide Maharashtra Fallback Baseline"
            : `District Benchmark: ${baseline.district}`}
        </Badge>
        <Badge variant="neutral">
          {formatCropLabel(baseline.crop_code)} · {baseline.data_period}
        </Badge>
        <Badge variant="outline">{baseline.sample_seasons_count} APY records</Badge>
      </div>

      {isStatewideFallback && (
        <div className="flex items-start gap-2.5 rounded-xl border border-[#f3d6c4] bg-[#fff7f0] p-3 text-xs leading-5 text-[#9a3700]">
          <Info size={16} className="mt-0.5 shrink-0" />
          <span>
            Fewer than 3 historical APY records were found specifically for{" "}
            <strong>{baseline.district}</strong> ({formatCropLabel(baseline.crop_code)}), so DES
            Maharashtra statewide records ({baseline.geographical_unit}) are shown instead.
          </span>
        </div>
      )}

      {hasStats ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <div className="rounded-xl border border-line bg-canvas p-3">
            <p className="text-[11px] font-bold text-muted">P10 (Poor Year)</p>
            <p className="mt-1 text-base font-extrabold text-ink">
              {formatNumber(baseline.historical_p10_t_ha, 2)} t/ha
            </p>
          </div>
          <div className="rounded-xl border border-line bg-canvas p-3">
            <p className="text-[11px] font-bold text-muted">P25 (Lower Quartile)</p>
            <p className="mt-1 text-base font-extrabold text-ink">
              {formatNumber(baseline.historical_p25_t_ha, 2)} t/ha
            </p>
          </div>
          <div className="rounded-xl border border-[#cde0ce] bg-[#f1f8f1] p-3">
            <p className="text-[11px] font-bold text-forest">Median (P50)</p>
            <p className="mt-1 text-base font-extrabold text-forest">
              {formatNumber(baseline.historical_median_t_ha, 2)} t/ha
            </p>
          </div>
          <div className="rounded-xl border border-[#cde0ce] bg-[#f1f8f1] p-3">
            <p className="text-[11px] font-bold text-forest">Mean Yield</p>
            <p className="mt-1 text-base font-extrabold text-forest">
              {formatNumber(baseline.historical_mean_t_ha, 2)} t/ha
            </p>
          </div>
          <div className="rounded-xl border border-line bg-canvas p-3">
            <p className="text-[11px] font-bold text-muted">P90 (Top Year)</p>
            <p className="mt-1 text-base font-extrabold text-ink">
              {formatNumber(baseline.historical_p90_t_ha, 2)} t/ha
            </p>
          </div>
          <div className="rounded-xl border border-line bg-canvas p-3">
            <p className="text-[11px] font-bold text-muted">Recorded Min–Max</p>
            <p className="mt-1 text-sm font-extrabold text-ink">
              {formatNumber(baseline.min_recorded_t_ha, 2)}–
              {formatNumber(baseline.max_recorded_t_ha, 2)} t/ha
            </p>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-line bg-canvas p-4 text-xs text-muted">
          Historical DES APY statistics are unavailable for {baseline.district} /{" "}
          {formatCropLabel(baseline.crop_code)} ({baseline.status}).
        </div>
      )}

      <p className="text-[11px] leading-5 text-muted">{baseline.disclaimer}</p>
    </div>
  );
}

function YieldBody() {
  const { farm, overview, cycleVersion, openCropDialog } = useRashkarShell();

  const [crops, setCrops] = useState<RashkarCanonicalCropItem[]>([]);
  const [previewCropCode, setPreviewCropCode] = useState<string>("");
  const [assessment, setAssessment] = useState<YieldRiskResponse | null>(null);
  const [history, setHistory] = useState<YieldHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // District x Crop baseline explorer
  const [lookupDistrict, setLookupDistrict] = useState<string>(farm?.district || "Pune");
  const [lookupCrop, setLookupCrop] = useState<string>("soybean");
  const [lookupResult, setLookupResult] = useState<HistoricalYieldBaseline | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    rashkarApi
      .listCrops(false)
      .then((list) => {
        if (mounted) setCrops(list);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (farm?.district) {
      setLookupDistrict(farm.district);
    }
  }, [farm?.id, farm?.district]);

  useEffect(() => {
    if (overview?.has_active_crop) {
      setPreviewCropCode("");
    }
  }, [overview?.has_active_crop, overview?.active_crop_cycle?.id]);

  const loadYield = useCallback(
    async (candidateCode?: string) => {
      if (!farm?.id) return;
      setLoading(true);
      setError(null);
      try {
        const [res, hist] = await Promise.all([
          rashkarApi.getYieldAssessment(farm.id, {
            cropCode: candidateCode || undefined,
          }),
          rashkarApi.getYieldHistory(farm.id, 10).catch(() => []),
        ]);
        setAssessment(res);
        setHistory(hist);
        if (res.crop_code) {
          setLookupCrop(res.crop_code);
        }
      } catch (err: any) {
        setError(err?.message || "Failed to load yield risk assessment.");
      } finally {
        setLoading(false);
      }
    },
    [farm?.id],
  );

  useEffect(() => {
    if (farm?.id) {
      loadYield(previewCropCode || undefined);
    }
  }, [farm?.id, cycleVersion, previewCropCode, loadYield]);

  const handleRunBaselineLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lookupDistrict.trim() || !lookupCrop.trim()) return;
    setLookupLoading(true);
    setLookupError(null);
    try {
      const data = await rashkarApi.getYieldBaseline(lookupDistrict.trim(), lookupCrop);
      setLookupResult(data);
    } catch (err: any) {
      setLookupError(err?.message || "Could not look up DES APY baseline.");
    } finally {
      setLookupLoading(false);
    }
  };

  if (!farm) return null;

  const isPreSowingPreview =
    assessment?.provenance?.screening_mode === "PRE_SOWING_PREVIEW" || Boolean(previewCropCode);

  if (loading && !assessment) {
    return (
      <Card>
        <CardContent className="py-12">
          <LoadingState label="Screening DES APY yield benchmarks and 5-dimension risks..." />
        </CardContent>
      </Card>
    );
  }

  if (error && !assessment) {
    return (
      <Card>
        <CardContent className="py-6">
          <ErrorState
            title="Could not load yield intelligence"
            description={error}
            action={
              <Button
                type="button"
                variant="secondary"
                onClick={() => loadYield(previewCropCode || undefined)}
              >
                <RefreshCw size={15} /> Try again
              </Button>
            }
          />
        </CardContent>
      </Card>
    );
  }

  if (!assessment) return null;

  // Honest NO_ACTIVE_CROP state with 2 explicit paths
  if (
    assessment.status === "NO_ACTIVE_CROP" ||
    !assessment.has_active_crop ||
    assessment.needs_crop_registration
  ) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="py-8">
            <EmptyState
              icon={Sprout}
              title="No active crop registered yet"
              description={
                assessment.message ||
                "Register your standing crop cycle OR screen a candidate crop before sowing to inspect district APY yield benchmarks and stress risks."
              }
            />

            <div className="mx-auto mt-2 grid max-w-2xl gap-4 sm:grid-cols-2">
              <div className="flex flex-col justify-between rounded-2xl border border-line bg-canvas p-4">
                <div>
                  <p className="text-sm font-extrabold text-ink">1. Register Active Crop</p>
                  <p className="mt-1 text-xs leading-5 text-muted">
                    Save what is currently planted on {farm.name} so all RASHKAR checks track real
                    field progress.
                  </p>
                </div>
                <Button type="button" className="mt-4 w-full" onClick={openCropDialog}>
                  <Plus size={15} /> Register Active Crop
                </Button>
              </div>

              <div className="flex flex-col justify-between rounded-2xl border border-[#b8d0ba] bg-[#f4faf4] p-4">
                <div>
                  <p className="text-sm font-extrabold text-forest">
                    2. Screen a Candidate Crop Before Sowing
                  </p>
                  <p className="mt-1 text-xs leading-5 text-muted">
                    Run a Pre-Sowing Preview without registering an active crop cycle.
                  </p>
                </div>
                <select
                  aria-label="Screen a Candidate Crop Before Sowing"
                  value={previewCropCode}
                  onChange={(e) => setPreviewCropCode(e.target.value)}
                  className="mt-4 min-h-11 w-full rounded-xl border border-line bg-white px-3 text-xs font-bold text-ink shadow-sm"
                >
                  <option value="">Choose candidate crop to preview...</option>
                  {crops.map((c) => (
                    <option key={c.crop_code} value={c.crop_code}>
                      {c.common_name_en} ({c.common_name_mr})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Honest WEATHER_UNAVAILABLE state
  if (assessment.status === "WEATHER_UNAVAILABLE") {
    return (
      <Card className="border-line bg-[#f7faf7]">
        <CardContent className="p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
            <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-[#eff3ef] text-muted">
              <CloudOff size={22} />
            </span>
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="neutral">WEATHER_UNAVAILABLE</Badge>
                {isPreSowingPreview && <Badge variant="orange">Pre-Sowing Preview</Badge>}
              </div>
              <h2 className="text-lg font-extrabold text-ink">
                Meteorological summary is currently unavailable
              </h2>
              <p className="text-sm leading-6 text-muted">
                {assessment.message ||
                  "Yield stress screening is paused because live/recent weather summary could not be obtained."}
              </p>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => loadYield(previewCropCode || undefined)}
              >
                <RefreshCw size={14} /> Retry
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const compositeTone = getRiskTone(assessment.composite_risk_tier);
  const gateLocked =
    assessment.ml_prediction_gate?.farm_level_supervised_model === "LOCKED_PENDING_CCE_LABELS" ||
    Boolean(assessment.ml_prediction_gate?.farm_level_supervised_model);
  const soil = assessment.suitability_analysis;

  return (
    <div className="space-y-6">
      {/* Pre-Sowing Preview Switcher Banner */}
      {isPreSowingPreview && (
        <Card className="border-[#f3d6c4] bg-[#fff7f0]">
          <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-2 text-xs text-[#9a3700]">
              <Badge variant="accent">Pre-Sowing Preview</Badge>
              <span>
                Screening candidate crop <strong>{assessment.crop_name}</strong> before sowing (no
                active cycle saved).
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                aria-label="Switch Candidate Crop"
                value={previewCropCode}
                onChange={(e) => setPreviewCropCode(e.target.value)}
                className="min-h-9 rounded-lg border border-line bg-white px-2.5 text-xs font-bold text-ink"
              >
                {crops.map((c) => (
                  <option key={c.crop_code} value={c.crop_code}>
                    {c.common_name_en}
                  </option>
                ))}
              </select>
              <Button type="button" size="sm" variant="primary" onClick={openCropDialog}>
                Register Active Crop
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mandatory Honest Prediction Lock Notice */}
      {gateLocked && (
        <div className="flex items-start gap-3 rounded-2xl border border-[#b7d1e6] bg-[#f2f7fc] p-4 text-xs leading-5 text-[#1b4a70] sm:text-sm">
          <Lock size={19} className="mt-0.5 shrink-0" />
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <strong>Plot-Level Harvest Tonnage Prediction Locked</strong>
              <Badge variant="outline" className="border-[#9ec1dd] bg-white text-[10px] text-[#1b4a70]">
                {assessment.ml_prediction_gate.farm_level_supervised_model ||
                  "LOCKED_PENDING_CCE_LABELS"}
              </Badge>
            </div>
            <p>
              {assessment.ml_prediction_gate.ethical_safeguard ||
                "Predicting exact farm-level harvest tonnage without verified multi-season Crop Cutting Experiment (CCE) or farmer harvest labels is intentionally disabled. Below are official DES APY historical district distributions (P10–P90) and live environmental stress screenings."}
            </p>
          </div>
        </div>
      )}

      {/* Summary & Composite Risk Header */}
      <Card>
        <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="green">
                {assessment.crop_name || formatCropLabel(assessment.crop_code)}
              </Badge>
              {isPreSowingPreview && <Badge variant="accent">Pre-Sowing Preview</Badge>}
              <Badge variant={compositeTone.badgeVariant}>
                Composite Risk: {compositeTone.label}
                {assessment.composite_risk_score != null
                  ? ` (${assessment.composite_risk_score.toFixed(1)}/100)`
                  : ""}
              </Badge>
            </div>
            <h2 className="text-lg font-extrabold text-ink">
              {assessment.farm_name} · {assessment.location_display}
            </h2>
            <p className="text-xs text-muted">
              Stage: <strong>{assessment.crop_stage?.stage_name_en || "General Growth"}</strong>
              {assessment.days_after_sowing != null ? ` (DAS ${assessment.days_after_sowing})` : ""}
              {assessment.irrigation_type ? ` · ${assessment.irrigation_type}` : ""}
              {assessment.total_area_acres != null
                ? ` · ${assessment.total_area_acres.toFixed(2)} acres`
                : ""}
            </p>
          </div>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            onClick={() => loadYield(previewCropCode || undefined)}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh Screening
          </Button>
        </CardContent>
      </Card>

      {/* DES Historical APY District Benchmark (1997-2021) */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 size={18} className="text-forest" />
                DES Historical APY District Benchmark (1997–2021)
              </CardTitle>
              <p className="mt-1 text-xs text-muted">
                Empirical yield distribution in tonnes per hectare (t/ha) from official Directorate
                of Economics & Statistics records.
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5 pt-2">
          {assessment.yield_baseline ? (
            <BaselineMetricsGrid baseline={assessment.yield_baseline} />
          ) : (
            <p className="text-xs text-muted">No baseline returned for this screening.</p>
          )}

          {/* Optional Inline District × Crop Lookup Switcher */}
          <form
            onSubmit={handleRunBaselineLookup}
            className="rounded-2xl border border-line bg-canvas p-4"
          >
            <p className="text-xs font-extrabold text-ink">
              Compare Another District × Crop APY Baseline
            </p>
            <div className="mt-2.5 grid gap-2.5 sm:grid-cols-3">
              <div>
                <Input
                  list="rashkar-mh-districts"
                  value={lookupDistrict}
                  onChange={(e) => setLookupDistrict(e.target.value)}
                  placeholder="District (e.g., Pune, Nashik)"
                  className="min-h-10 text-xs"
                />
                <datalist id="rashkar-mh-districts">
                  {MAHARASHTRA_DISTRICTS.map((d) => (
                    <option key={d} value={d} />
                  ))}
                </datalist>
              </div>
              <select
                aria-label="Lookup Crop"
                value={lookupCrop}
                onChange={(e) => setLookupCrop(e.target.value)}
                className="min-h-10 w-full rounded-xl border border-line bg-white px-3 text-xs font-bold text-ink"
              >
                {(crops.length > 0
                  ? crops
                  : [
                      { crop_code: "soybean", common_name_en: "Soybean" },
                      { crop_code: "cotton", common_name_en: "Cotton" },
                      { crop_code: "jowar", common_name_en: "Jowar / Sorghum" },
                      { crop_code: "sugarcane", common_name_en: "Sugarcane" },
                      { crop_code: "onion", common_name_en: "Onion" },
                      { crop_code: "wheat", common_name_en: "Wheat" },
                    ]
                ).map((c) => (
                  <option key={c.crop_code} value={c.crop_code}>
                    {c.common_name_en}
                  </option>
                ))}
              </select>
              <Button type="submit" size="sm" variant="secondary" disabled={lookupLoading}>
                {lookupLoading ? (
                  <>
                    <LoaderCircle size={14} className="animate-spin" /> Loading...
                  </>
                ) : (
                  <>
                    <Search size={14} /> Check APY Baseline
                  </>
                )}
              </Button>
            </div>
            {lookupError && (
              <p className="mt-2 text-xs font-semibold text-[#b71c1c]">{lookupError}</p>
            )}
            {lookupResult && (
              <div className="mt-4 rounded-xl border border-line bg-white p-4">
                <BaselineMetricsGrid baseline={lookupResult} />
              </div>
            )}
          </form>
        </CardContent>
      </Card>

      {/* 5-Dimension Environmental & Soil Risk Screening */}
      <section aria-label="5-dimension risk screening">
        <SectionHeader
          title="5-Dimension Environmental & Soil Risk Screening"
          description="Biophysical stresses evaluated across weather forecasts, rainfall patterns, soil records, heat thresholds, and humidity."
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {assessment.risks.map((risk, idx) => {
            const tone = getRiskTone(risk.risk_level);
            return (
              <Card key={`${risk.risk_dimension}-${idx}`}>
                <CardContent className="space-y-3 p-5">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-sm font-extrabold text-ink">
                      {RISK_DIMENSION_LABELS[risk.risk_dimension] ||
                        formatTokenLabel(risk.risk_dimension)}
                    </h3>
                    <Badge variant={tone.badgeVariant}>{tone.label}</Badge>
                  </div>

                  <div className="flex flex-wrap gap-1.5 text-[10px]">
                    <Badge variant="outline">Horizon: {formatTokenLabel(risk.time_horizon)}</Badge>
                    <Badge variant="outline">
                      Confidence: {formatTokenLabel(risk.confidence)}
                    </Badge>
                  </div>

                  <ul className="space-y-1 text-xs leading-5 text-muted">
                    {risk.drivers.map((drv, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-leaf" />
                        <span>{drv}</span>
                      </li>
                    ))}
                  </ul>

                  {risk.recommended_actions?.length > 0 && (
                    <div className="space-y-1.5 rounded-xl border border-[#dce8dc] bg-[#f4faf4] p-3 text-xs">
                      {risk.recommended_actions.map((act, i) => (
                        <div key={i}>
                          {act.title && <p className="font-bold text-forest">{act.title}</p>}
                          {act.description && <p className="text-ink/85">{act.description}</p>}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Soil Suitability + Actionable Recommendations */}
      <section className="grid gap-4 lg:grid-cols-12">
        {soil && (
          <Card className="lg:col-span-5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers size={18} className="text-soil" /> Soil Suitability Profile
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-3 text-xs">
              <div className="rounded-xl border border-line bg-canvas p-3">
                <p className="font-extrabold text-ink">{soil.suitability_verdict}</p>
                <p className="mt-1 text-[11px] text-muted">Source: {soil.data_provenance}</p>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div className="rounded-xl border border-line p-3">
                  <span className="text-[11px] text-muted">Soil Texture</span>
                  <p className="mt-0.5 font-bold text-ink">
                    {soil.soil_texture || "Data Not Available"}
                  </p>
                </div>
                <div className="rounded-xl border border-line p-3">
                  <span className="text-[11px] text-muted">Soil pH</span>
                  <p className="mt-0.5 font-bold text-ink">
                    {soil.soil_ph != null
                      ? `${soil.soil_ph.toFixed(1)} (${soil.ph_status})`
                      : "Data Not Available"}
                  </p>
                </div>
                <div className="rounded-xl border border-line p-3">
                  <span className="text-[11px] text-muted">Organic Carbon</span>
                  <p className="mt-0.5 font-bold text-ink">
                    {soil.organic_carbon_pct != null
                      ? `${soil.organic_carbon_pct.toFixed(2)}%`
                      : "Data Not Available"}
                  </p>
                </div>
                <div className="rounded-xl border border-line p-3">
                  <span className="text-[11px] text-muted">Available Water Cap.</span>
                  <p className="mt-0.5 font-bold text-ink">
                    {soil.available_water_capacity_mm_m != null
                      ? `${soil.available_water_capacity_mm_m.toFixed(0)} mm/m`
                      : "Data Not Available"}
                  </p>
                </div>
                <div className="rounded-xl border border-line p-3">
                  <span className="text-[11px] text-muted">Rooting Depth</span>
                  <p className="mt-0.5 font-bold text-ink">
                    {soil.effective_rooting_depth_cm != null
                      ? `${soil.effective_rooting_depth_cm.toFixed(0)} cm`
                      : "Data Not Available"}
                  </p>
                </div>
                <div className="rounded-xl border border-line p-3">
                  <span className="text-[11px] text-muted">District Normal Rain</span>
                  <p className="mt-0.5 font-bold text-ink">
                    {soil.climate_normal_rainfall_mm != null
                      ? `${soil.climate_normal_rainfall_mm.toFixed(0)} mm`
                      : "Data Not Available"}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Card className={soil ? "lg:col-span-7" : "lg:col-span-12"}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert size={18} className="text-leaf" /> Actionable Yield Protection Steps
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pt-3">
            {assessment.recommendations.map((rec) => (
              <div key={rec.recommendation_id} className="rounded-2xl border border-line p-4 text-xs">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="text-sm font-extrabold text-ink">{rec.title}</h4>
                  <Badge variant={rec.urgency.toLowerCase() === "high" ? "orange" : "green"}>
                    {rec.urgency} Urgency
                  </Badge>
                </div>
                <p className="mt-1.5 leading-5 text-ink/90">{rec.description}</p>
                <p className="mt-1.5 leading-5 text-muted">
                  <strong className="text-ink">Why:</strong> {rec.why_recommended}
                </p>
                <p className="mt-1 text-[11px] text-muted">
                  <strong>Supporting Data:</strong> {rec.supporting_data} ·{" "}
                  <strong>Source:</strong> {rec.evidence_source}
                </p>
                <p className="mt-1 text-[11px] text-[#9a3700]">
                  <strong>Limitation:</strong> {rec.limitations}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      {/* More Details Panel */}
      <MoreDetailsPanel
        title="More Details — Narrative, Coverage, Provenance & ML Prediction Gate"
        subtitle="Inspect plain-language agronomic narrative, data provenance, and harvest-label lock details."
        badgeText="DES APY · Provenance"
      >
        <div className="space-y-4 text-xs">
          {assessment.farmer_narrative_explanation && (
            <div className="rounded-xl border border-line bg-white p-4 leading-6 text-ink">
              <p className="font-extrabold text-forest">Agronomic Summary Narrative</p>
              <p className="mt-1">{assessment.farmer_narrative_explanation}</p>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-line bg-white p-4">
              <p className="font-extrabold text-ink">Coverage & Geographical Scope</p>
              <dl className="mt-2 space-y-1 text-muted">
                {Object.entries(assessment.coverage || {}).map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-2">
                    <dt>{formatTokenLabel(k)}:</dt>
                    <dd className="font-bold text-ink">{String(v ?? "—")}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="rounded-xl border border-line bg-white p-4">
              <p className="font-extrabold text-ink">Data Provenance & Gate Status</p>
              <dl className="mt-2 space-y-1 text-muted">
                <div className="flex justify-between gap-2">
                  <dt>Prediction Gate:</dt>
                  <dd className="font-bold text-ink">
                    {assessment.ml_prediction_gate.farm_level_supervised_model || "LOCKED"}
                  </dd>
                </div>
                {Object.entries(assessment.provenance || {}).map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-2">
                    <dt>{formatTokenLabel(k)}:</dt>
                    <dd className="font-bold text-ink">{String(v ?? "—")}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        </div>
      </MoreDetailsPanel>

      {/* Farm Yield History */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History size={17} className="text-leaf" /> Yield Screening History
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-3">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] text-left text-xs">
                <thead>
                  <tr className="border-b border-line text-[11px] font-extrabold uppercase tracking-wider text-muted">
                    <th className="py-2 pr-3">Assessed (IST)</th>
                    <th className="py-2 pr-3">Crop</th>
                    <th className="py-2 pr-3">Benchmark Tier</th>
                    <th className="py-2 pr-3">APY Mean</th>
                    <th className="py-2 pr-3">Composite Risk</th>
                    <th className="py-2">ML Gate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/60">
                  {history.map((row) => {
                    const tone = getRiskTone(row.composite_risk_tier);
                    return (
                      <tr key={row.id}>
                        <td className="py-2.5 pr-3 font-semibold text-ink">
                          {row.assessed_at_ist}
                        </td>
                        <td className="py-2.5 pr-3 font-bold text-ink">
                          {formatCropLabel(row.crop_code)}
                        </td>
                        <td className="py-2.5 pr-3 text-muted">
                          {formatTokenLabel(row.benchmark_tier)} ({row.apy_sample_count} yrs)
                        </td>
                        <td className="py-2.5 pr-3 text-ink">
                          {row.apy_mean_t_ha != null ? `${row.apy_mean_t_ha.toFixed(2)} t/ha` : "—"}
                        </td>
                        <td className="py-2.5 pr-3">
                          <Badge variant={tone.badgeVariant}>{tone.label}</Badge>
                        </td>
                        <td className="py-2.5 text-[11px] text-muted">
                          {row.prediction_lock_status}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export function YieldScreen() {
  return (
    <RashkarShell
      activeTab="yield"
      eyebrow="RASHKAR · Yield Intelligence"
      title="What risk does my crop yield face?"
      description="Official DES APY historical district benchmarks (1997–2021), 5-dimension biophysical stress screening, and honest harvest-prediction gating."
    >
      <YieldBody />
    </RashkarShell>
  );
}
