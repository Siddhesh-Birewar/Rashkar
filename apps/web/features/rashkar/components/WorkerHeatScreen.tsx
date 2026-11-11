"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  Clock,
  CloudOff,
  Droplets,
  HeartPulse,
  History,
  LoaderCircle,
  PhoneCall,
  RefreshCw,
  ShieldAlert,
  Sun,
  ThermometerSun,
  Wind,
} from "lucide-react";
import { ErrorState, LoadingState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/section-header";
import { rashkarApi, resolveValidFarmCoordinates } from "../lib/api";
import { formatTokenLabel, getRiskTone } from "../lib/format";
import type {
  ClothingType,
  SunExposureType,
  WorkerHeatAssessmentResponse,
  WorkerHeatHistoryItem,
  WorkloadCategory,
} from "../types";
import { MoreDetailsPanel } from "./MoreDetailsPanel";
import { RashkarShell, useRashkarShell } from "./RashkarShell";

const WORKLOAD_OPTIONS: Array<{ value: WorkloadCategory; label: string }> = [
  { value: "light", label: "Light (Seeding / Weeding)" },
  { value: "moderate", label: "Moderate (Spraying / Harvest)" },
  { value: "heavy", label: "Heavy (Tilling / Hauling)" },
  { value: "very_heavy", label: "Very Heavy (Intense Digging)" },
];

const CLOTHING_OPTIONS: Array<{ value: ClothingType; label: string }> = [
  { value: "standard_work_clothes", label: "Cotton Workwear (0°C CAV)" },
  { value: "coveralls_protective", label: "Coveralls (+2°C CAV)" },
  { value: "woven_double_layer", label: "Double-Layer (+3°C CAV)" },
  { value: "impermeable_vapor_barrier", label: "Spray Suit (+10°C CAV)" },
];

const SUN_OPTIONS: Array<{ value: SunExposureType; label: string }> = [
  { value: "direct_sun", label: "Direct Sun" },
  { value: "partial_shade", label: "Partial Shade" },
  { value: "full_shade", label: "Full Shade" },
];

const SHIFT_HOURS = [2, 4, 6, 8];

function WorkerHeatBody() {
  const { farm } = useRashkarShell();

  const [workload, setWorkload] = useState<WorkloadCategory>("moderate");
  const [clothing, setClothing] = useState<ClothingType>("standard_work_clothes");
  const [isAcclimatised, setIsAcclimatised] = useState<boolean>(true);
  const [sunExposure, setSunExposure] = useState<SunExposureType>("direct_sun");
  const [shiftHours, setShiftHours] = useState<number>(4);

  const [assessment, setAssessment] = useState<WorkerHeatAssessmentResponse | null>(null);
  const [history, setHistory] = useState<WorkerHeatHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAssessment = useCallback(async () => {
    if (!farm?.id) return;
    setLoading(true);
    setError(null);
    const coords = resolveValidFarmCoordinates(farm);
    try {
      const [res, hist] = await Promise.all([
        rashkarApi.assessWorkerHeat({
          farm_id: farm.id,
          ...coords,
          taluka: farm.taluka || undefined,
          workload_category: workload,
          clothing_type: clothing,
          is_acclimatised: isAcclimatised,
          sun_exposure: sunExposure,
          exposure_duration_hours: shiftHours,
        }),
        rashkarApi.getWorkerHeatHistory(farm.id, 10).catch(() => []),
      ]);
      setAssessment(res);
      setHistory(hist);
    } catch (err: any) {
      setError(err?.message || "Failed to calculate worker WBGT heat safety.");
    } finally {
      setLoading(false);
    }
  }, [farm?.id, farm?.taluka, workload, clothing, isAcclimatised, sunExposure, shiftHours]);

  useEffect(() => {
    if (farm?.id) {
      runAssessment();
    }
  }, [runAssessment, farm?.id]);

  if (!farm) return null;

  const isUnavailable = assessment?.status === "WEATHER_UNAVAILABLE";
  const currentProj = assessment?.hourly_projections?.[0];
  const currentTone = getRiskTone(assessment?.current_hazard_level);
  const maxTone = getRiskTone(assessment?.max_hazard_level_in_window);

  return (
    <div className="space-y-6">
      {/* Interactive Parameter Bar */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle>Work Conditions & Protective Gear</CardTitle>
              <p className="mt-1 text-xs text-muted">
                Adjust task intensity, clothing, acclimatisation, sun exposure, and shift length to
                update ISO 7243 / ACGIH screening limits.
              </p>
            </div>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={runAssessment}
              disabled={loading}
              className="shrink-0"
            >
              {loading ? (
                <>
                  <LoaderCircle size={14} className="animate-spin" /> Updating...
                </>
              ) : (
                <>
                  <RefreshCw size={14} /> Recalculate
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 pt-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          <div>
            <label className="text-xs font-extrabold text-ink">Workload Intensity</label>
            <select
              aria-label="Workload Intensity"
              value={workload}
              onChange={(e) => setWorkload(e.target.value as WorkloadCategory)}
              className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-white px-3 text-xs font-semibold text-ink shadow-sm"
            >
              {WORKLOAD_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-extrabold text-ink">Clothing Type</label>
            <select
              aria-label="Clothing Type"
              value={clothing}
              onChange={(e) => setClothing(e.target.value as ClothingType)}
              className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-white px-3 text-xs font-semibold text-ink shadow-sm"
            >
              {CLOTHING_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-extrabold text-ink">Sun Exposure</label>
            <select
              aria-label="Sun Exposure"
              value={sunExposure}
              onChange={(e) => setSunExposure(e.target.value as SunExposureType)}
              className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-white px-3 text-xs font-semibold text-ink shadow-sm"
            >
              {SUN_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-extrabold text-ink">Worker Acclimatised?</label>
            <button
              type="button"
              role="switch"
              aria-checked={isAcclimatised}
              onClick={() => setIsAcclimatised((v) => !v)}
              className={`mt-1.5 flex min-h-11 w-full items-center justify-between rounded-xl border px-3 text-xs font-bold transition ${
                isAcclimatised
                  ? "border-[#b8d0ba] bg-[#eef7ee] text-forest"
                  : "border-[#efb89c] bg-[#fff5ef] text-accent"
              }`}
            >
              <span>{isAcclimatised ? "Acclimatised" : "Unacclimatised (-3°C)"}</span>
              <Badge variant={isAcclimatised ? "green" : "orange"}>
                {isAcclimatised ? "YES" : "NO"}
              </Badge>
            </button>
          </div>

          <div>
            <label className="text-xs font-extrabold text-ink">Planned Shift Hours</label>
            <div className="mt-1.5 grid grid-cols-4 gap-1.5">
              {SHIFT_HOURS.map((hrs) => (
                <button
                  key={hrs}
                  type="button"
                  onClick={() => setShiftHours(hrs)}
                  className={`min-h-11 rounded-xl border text-xs font-extrabold transition ${
                    shiftHours === hrs
                      ? "border-forest bg-forest text-white shadow-sm"
                      : "border-line bg-white text-ink hover:bg-[#f3f8f3]"
                  }`}
                >
                  {hrs}h
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card>
          <CardContent className="py-6">
            <ErrorState
              title="Worker heat check failed"
              description={error}
              action={
                <Button type="button" variant="secondary" onClick={runAssessment}>
                  Retry assessment
                </Button>
              }
            />
          </CardContent>
        </Card>
      )}

      {loading && !assessment && (
        <Card>
          <CardContent className="py-12">
            <LoadingState label="Fetching live Open-Meteo hourly feed and solving WBGT..." />
          </CardContent>
        </Card>
      )}

      {/* Honest WEATHER_UNAVAILABLE State */}
      {assessment && isUnavailable && (
        <Card className="border-line bg-[#f7faf7]">
          <CardContent className="p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
              <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-[#eff3ef] text-muted">
                <CloudOff size={22} />
              </span>
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="neutral">WEATHER_UNAVAILABLE</Badge>
                  <Badge variant="outline">{assessment.farm_location_display}</Badge>
                </div>
                <h2 className="text-lg font-extrabold text-ink">
                  Live weather feed is currently unavailable
                </h2>
                <p className="text-sm leading-6 text-muted">
                  {assessment.error_message ||
                    "Hourly meteorological forecast could not be fetched for your farm coordinates. Worker WBGT calculation is paused rather than showing synthetic fallback temperatures."}
                </p>
                {assessment.missing_variables_warning && (
                  <p className="text-xs font-semibold text-muted">
                    {assessment.missing_variables_warning}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Full Worker Heat Safety Assessment */}
      {assessment && !isUnavailable && (
        <>
          {/* Primary Verdict Card */}
          <Card className={`border ${currentTone.surfaceClass}`}>
            <CardContent className="space-y-5 p-5 sm:p-6">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={currentTone.badgeVariant}>
                      NOW: {currentTone.label} HAZARD
                    </Badge>
                    <Badge variant={maxTone.badgeVariant}>
                      0–6H PEAK: {maxTone.label}
                    </Badge>
                    <Badge variant="outline" className="bg-white/80">
                      Action Limit: {assessment.screening_threshold_c.toFixed(1)}°C WBGT
                    </Badge>
                  </div>

                  <h2 className="text-xl font-extrabold tracking-[-0.025em] text-ink sm:text-2xl">
                    {currentProj?.work_rest_cycle || "Review work/rest schedule below"}
                  </h2>

                  <p className="max-w-3xl text-sm leading-6 text-ink/90">
                    {assessment.threshold_comparison_message}
                  </p>
                  {assessment.category_selection_reason && (
                    <p className="max-w-3xl text-xs leading-5 text-ink/75">
                      {assessment.category_selection_reason}
                    </p>
                  )}
                </div>

                {/* Live Environmental Readout Pills */}
                <div className="grid shrink-0 grid-cols-2 gap-2.5 sm:grid-cols-4 lg:grid-cols-2">
                  <div className="rounded-xl border border-line/80 bg-white/90 px-3.5 py-2.5">
                    <p className="text-[11px] font-bold text-muted">Effective WBGT Now</p>
                    <p className="mt-0.5 text-lg font-extrabold text-ink">
                      {currentProj ? `${currentProj.wbgt_effective_c.toFixed(1)}°C` : "—"}
                    </p>
                  </div>
                  <div className="rounded-xl border border-line/80 bg-white/90 px-3.5 py-2.5">
                    <p className="text-[11px] font-bold text-muted">Peak 6h WBGT</p>
                    <p className="mt-0.5 text-lg font-extrabold text-ink">
                      {assessment.max_wbgt_effective_c != null
                        ? `${assessment.max_wbgt_effective_c.toFixed(1)}°C`
                        : "—"}
                    </p>
                  </div>
                  <div className="rounded-xl border border-line/80 bg-white/90 px-3.5 py-2.5">
                    <p className="text-[11px] font-bold text-muted">Air Temp & RH</p>
                    <p className="mt-0.5 text-sm font-extrabold text-ink">
                      {assessment.current_air_temp_c != null
                        ? `${assessment.current_air_temp_c.toFixed(1)}°C`
                        : "—"}{" "}
                      ·{" "}
                      {assessment.current_relative_humidity_pct != null
                        ? `${assessment.current_relative_humidity_pct.toFixed(0)}%`
                        : "—"}
                    </p>
                  </div>
                  <div className="rounded-xl border border-line/80 bg-white/90 px-3.5 py-2.5">
                    <p className="text-[11px] font-bold text-muted">Wind & Solar</p>
                    <p className="mt-0.5 text-sm font-extrabold text-ink">
                      {assessment.current_wind_speed_kmh != null
                        ? `${assessment.current_wind_speed_kmh.toFixed(1)} km/h`
                        : "—"}{" "}
                      ·{" "}
                      {assessment.current_solar_radiation_wm2 != null
                        ? `${Math.round(assessment.current_solar_radiation_wm2)} W/m²`
                        : "—"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Peak Risk Hour Warning */}
              {(assessment.peak_risk_hour_ist || assessment.peak_risk_reason) && (
                <div className="flex items-start gap-3 rounded-xl border border-line/90 bg-white/85 p-3.5">
                  <Clock size={18} className="mt-0.5 shrink-0 text-accent" />
                  <div className="text-xs leading-5 text-ink">
                    <strong>Peak Risk Hour ({assessment.peak_risk_hour_ist || "Next 6h"}):</strong>{" "}
                    {assessment.peak_risk_reason}
                  </div>
                </div>
              )}

              {/* Shift Coverage Limitation Warning (e.g. 8h shift vs 6h forecast) */}
              {assessment.shift_exceeds_forecast_coverage && assessment.coverage_limitation_warning && (
                <div className="flex items-start gap-3 rounded-xl border border-[#f3d6c4] bg-[#fff7f0] p-3.5 text-xs leading-5 text-[#9a3700]">
                  <AlertTriangle size={17} className="mt-0.5 shrink-0" />
                  <span>{assessment.coverage_limitation_warning}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 0–6h Hourly Projection Grid */}
          <section aria-label="0 to 6 hour WBGT projections">
            <SectionHeader
              title="0–6 Hour Outdoor Safety Timeline"
              description={`Valid ${assessment.valid_time_ist} · Source: ${assessment.weather_source_name}`}
            />
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
              {assessment.hourly_projections.map((pt) => {
                const tone = getRiskTone(pt.hazard_level);
                return (
                  <Card
                    key={pt.forecast_hour_offset}
                    className={
                      pt.exceeds_screening_threshold ? "border-[#efb89c]" : "border-line"
                    }
                  >
                    <CardContent className="space-y-2.5 p-4">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-extrabold text-ink">
                          {pt.forecast_hour_offset === 0
                            ? `Now (${pt.valid_time_ist})`
                            : `+${pt.forecast_hour_offset}h · ${pt.valid_time_ist}`}
                        </span>
                      </div>

                      <div className="flex items-baseline justify-between">
                        <div>
                          <p className="text-[11px] text-muted">Eff. WBGT</p>
                          <p className="text-lg font-extrabold text-ink">
                            {pt.wbgt_effective_c.toFixed(1)}°C
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-[11px] text-muted">Air Temp</p>
                          <p className="text-sm font-bold text-ink">
                            {pt.air_temp_c.toFixed(1)}°C
                          </p>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-1.5">
                        <Badge variant={tone.badgeVariant}>{tone.label}</Badge>
                        {pt.exceeds_screening_threshold && (
                          <Badge variant="destructive" className="text-[10px]">
                            Exceeds Limit
                          </Badge>
                        )}
                      </div>

                      <p className="text-[11px] font-semibold leading-4 text-ink">
                        {pt.work_rest_cycle}
                      </p>
                      <p className="text-[10px] text-muted">
                        RH {pt.relative_humidity_pct.toFixed(0)}% · Trend{" "}
                        {formatTokenLabel(pt.trend)}
                      </p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </section>

          {/* Practical Safety Guidance & Hydration */}
          <section className="grid gap-4 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sun size={18} className="text-leaf" /> Before & During Work
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-3 text-xs leading-5">
                <div>
                  <p className="font-extrabold uppercase tracking-wider text-forest">
                    Before heading out
                  </p>
                  <ul className="mt-1.5 list-disc space-y-1.5 pl-4 text-ink/90">
                    {assessment.before_work_guidance.map((tip, i) => (
                      <li key={i}>{tip}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="font-extrabold uppercase tracking-wider text-forest">
                    During field work
                  </p>
                  <ul className="mt-1.5 list-disc space-y-1.5 pl-4 text-ink/90">
                    {assessment.during_work_guidance.map((tip, i) => (
                      <li key={i}>{tip}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Droplets size={18} className="text-calm" /> Hydration & Electrolytes
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 pt-3 text-xs leading-5">
                {assessment.hydration_guidance.rule_summary && (
                  <p className="font-semibold text-ink">
                    {assessment.hydration_guidance.rule_summary}
                  </p>
                )}
                {assessment.hydration_guidance.electrolyte_advice && (
                  <p className="text-muted">
                    <strong className="text-ink">Electrolytes:</strong>{" "}
                    {assessment.hydration_guidance.electrolyte_advice}
                  </p>
                )}
                {assessment.hydration_guidance.max_hourly_rate && (
                  <div className="rounded-xl border border-[#f3d6c4] bg-[#fff7f0] p-3 text-[#9a3700]">
                    {assessment.hydration_guidance.max_hourly_rate}
                  </div>
                )}
                {assessment.hydration_guidance.beverage_restrictions && (
                  <p className="text-[11px] text-muted">
                    {assessment.hydration_guidance.beverage_restrictions}
                  </p>
                )}
              </CardContent>
            </Card>

            <Card className="border-[#f2b8b5]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-[#b71c1c]">
                  <ShieldAlert size={18} /> Emergency Heat Triage
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 pt-3 text-xs leading-5">
                {assessment.emergency_triage.heat_exhaustion && (
                  <div>
                    <p className="font-extrabold text-ink">Heat Exhaustion (Cool & Sip ORS)</p>
                    <p className="mt-1 text-muted">
                      Signs:{" "}
                      {assessment.emergency_triage.heat_exhaustion.warning_signs?.join("; ")}
                    </p>
                    <p className="mt-1 text-ink">
                      Action:{" "}
                      {assessment.emergency_triage.heat_exhaustion.immediate_response?.[0]}{" "}
                      {assessment.emergency_triage.heat_exhaustion.immediate_response?.[2]}
                    </p>
                  </div>
                )}

                {assessment.emergency_triage.heat_stroke && (
                  <div className="rounded-xl border border-[#f2b8b5] bg-[#fdeeee] p-3">
                    <p className="font-extrabold text-[#b71c1c]">
                      Heat Stroke — Medical Emergency
                    </p>
                    <p className="mt-1 text-[#7f1d1d]">
                      Signs: {assessment.emergency_triage.heat_stroke.warning_signs?.join("; ")}
                    </p>
                    <ul className="mt-1.5 list-disc space-y-1 pl-4 font-semibold text-[#7f1d1d]">
                      {assessment.emergency_triage.heat_stroke.immediate_response
                        ?.slice(0, 3)
                        .map((act, idx) => <li key={idx}>{act}</li>)}
                    </ul>
                  </div>
                )}

                {Object.keys(assessment.local_emergency_contacts || {}).length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {Object.entries(assessment.local_emergency_contacts).map(([k, v]) => (
                      <Badge key={k} variant="outline" className="gap-1 py-1 text-[10px]">
                        <PhoneCall size={11} /> {v}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          {/* More Technical & Scientific Details */}
          <MoreDetailsPanel
            title="More Technical Details — WBGT, Heat Index, UTCI & Topographic Downscaling"
            subtitle="Physics solver outputs, personalized heat strain sub-indices, and ACGIH 2023 / ISO 7243 disclaimers."
            badgeText="ACGIH 2023 · ISO 7243:2017"
          >
            <div className="space-y-5 text-xs">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border border-line bg-white p-3.5">
                  <p className="text-muted font-bold">WBGT (Effective / CAV)</p>
                  <p className="mt-1 text-base font-extrabold text-ink">
                    {assessment.current_wbgt_estimated_c != null
                      ? `${assessment.current_wbgt_estimated_c.toFixed(1)}°C`
                      : "—"}{" "}
                    <span className="text-xs font-semibold text-muted">
                      (CAV +{assessment.clothing_cav_c.toFixed(1)}°C)
                    </span>
                  </p>
                </div>
                <div className="rounded-xl border border-line bg-white p-3.5">
                  <p className="text-muted font-bold">NOAA Heat Index</p>
                  <p className="mt-1 text-base font-extrabold text-ink">
                    {assessment.current_heat_index_c != null
                      ? `${assessment.current_heat_index_c.toFixed(1)}°C`
                      : "—"}
                  </p>
                </div>
                <div className="rounded-xl border border-line bg-white p-3.5">
                  <p className="text-muted font-bold">UTCI (Approx.)</p>
                  <p className="mt-1 text-base font-extrabold text-ink">
                    {assessment.current_utci_c != null
                      ? `${assessment.current_utci_c.toFixed(1)}°C`
                      : "—"}
                  </p>
                </div>
                <div className="rounded-xl border border-line bg-white p-3.5">
                  <p className="text-muted font-bold">Dew Point</p>
                  <p className="mt-1 text-base font-extrabold text-ink">
                    {assessment.current_dew_point_c != null
                      ? `${assessment.current_dew_point_c.toFixed(1)}°C`
                      : "—"}
                  </p>
                </div>
              </div>

              {assessment.personalized_heat_strain_score && (
                <div className="rounded-xl border border-line bg-white p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-extrabold text-ink">
                      Personalized Worker Heat Strain Score:{" "}
                      {assessment.personalized_heat_strain_score.score_0_100}/100
                    </p>
                    <Badge variant="neutral">
                      {formatTokenLabel(
                        assessment.personalized_heat_strain_score.severity_level,
                      )}
                    </Badge>
                  </div>
                  {assessment.personalized_heat_strain_score.action_summary && (
                    <p className="mt-1.5 text-muted">
                      {assessment.personalized_heat_strain_score.action_summary}
                    </p>
                  )}
                  {assessment.personalized_heat_strain_score.sub_indices && (
                    <div className="mt-3 grid gap-2 sm:grid-cols-4">
                      {Object.entries(
                        assessment.personalized_heat_strain_score.sub_indices,
                      ).map(([key, val]) => (
                        <div key={key} className="rounded-lg bg-canvas px-3 py-2">
                          <span className="block text-[10px] text-muted">
                            {formatTokenLabel(key)}
                          </span>
                          <span className="font-bold text-ink">{val} pts</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {assessment.topographic_downscaling && (
                <div className="rounded-xl border border-line bg-white p-4">
                  <p className="font-extrabold text-ink">Topographic Downscaling</p>
                  <p className="mt-1 text-muted">
                    {assessment.topographic_downscaling.methodology} · Grid{" "}
                    {assessment.topographic_downscaling.base_grid_resolution_km} km → Target{" "}
                    {assessment.topographic_downscaling.target_plot_resolution_km} km · Status:{" "}
                    <strong>
                      {formatTokenLabel(String(assessment.topographic_downscaling.status || ""))}
                    </strong>
                    {assessment.topographic_downscaling.downscaled_plot_temp_c != null
                      ? ` · Plot temp ${assessment.topographic_downscaling.downscaled_plot_temp_c}°C (lapse adj ${assessment.topographic_downscaling.lapse_adjustment_c}°C)`
                      : ""}
                  </p>
                </div>
              )}

              <div className="space-y-2 rounded-xl border border-line bg-white p-4 text-muted">
                <p>
                  <strong className="text-ink">Standards & Solver:</strong>{" "}
                  {assessment.methodology_reference} ({assessment.methodology_standards_version})
                </p>
                {assessment.threshold_meaning_explanation && (
                  <p>{assessment.threshold_meaning_explanation}</p>
                )}
                {assessment.safety_guarantee_disclaimer && (
                  <p>{assessment.safety_guarantee_disclaimer}</p>
                )}
                <p className="font-semibold text-ink">{assessment.disclaimer}</p>
              </div>
            </div>
          </MoreDetailsPanel>
        </>
      )}

      {/* Farm Worker-Heat Audit Log History */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History size={17} className="text-leaf" /> Recent Farm Worker Heat Checks
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-3">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] text-left text-xs">
                <thead>
                  <tr className="border-b border-line text-[11px] font-extrabold uppercase tracking-wider text-muted">
                    <th className="py-2 pr-3">Time (IST)</th>
                    <th className="py-2 pr-3">Workload</th>
                    <th className="py-2 pr-3">WBGT / Limit</th>
                    <th className="py-2 pr-3">Hazard</th>
                    <th className="py-2 pr-3">Air Temp / RH</th>
                    <th className="py-2">Provider</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/60">
                  {history.map((item) => {
                    const tone = getRiskTone(item.risk_tier);
                    return (
                      <tr key={item.id}>
                        <td className="py-2.5 pr-3 font-semibold text-ink">
                          {item.request_timestamp_ist}
                        </td>
                        <td className="py-2.5 pr-3 text-muted">
                          {formatTokenLabel(item.workload_class)} (
                          {item.acclimatization_status ? "Acclim." : "Unacclim."})
                        </td>
                        <td className="py-2.5 pr-3 font-bold text-ink">
                          {item.calculated_wbgt_c.toFixed(1)}°C /{" "}
                          {item.applied_threshold_wbgt_c.toFixed(1)}°C
                        </td>
                        <td className="py-2.5 pr-3">
                          <Badge variant={tone.badgeVariant}>{tone.label}</Badge>
                        </td>
                        <td className="py-2.5 pr-3 text-muted">
                          {item.air_temp_c.toFixed(1)}°C · {item.relative_humidity_pct.toFixed(0)}%
                        </td>
                        <td className="py-2.5 text-muted">{item.weather_provider}</td>
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

export function WorkerHeatScreen() {
  return (
    <RashkarShell
      activeTab="worker-heat"
      eyebrow="RASHKAR · Worker Heat & WBGT"
      title="Can I work outside now?"
      description="Occupational heat hazard screening using Open-Meteo hourly forecasts, Liljegren WBGT physics, and ACGIH 2023 / ISO 7243 work-rest limits."
    >
      <WorkerHeatBody />
    </RashkarShell>
  );
}
