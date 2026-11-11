"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  CloudOff,
  Flame,
  History,
  Layers,
  LoaderCircle,
  Moon,
  Plus,
  RefreshCw,
  ShieldCheck,
  Sprout,
  Thermometer,
} from "lucide-react";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/section-header";
import { rashkarApi } from "../lib/api";
import { formatCropLabel, formatTokenLabel, getRiskTone } from "../lib/format";
import type { CropHeatAssessmentResponse, CropHeatHistoryItem } from "../types";
import { MoreDetailsPanel } from "./MoreDetailsPanel";
import { RashkarShell, useRashkarShell } from "./RashkarShell";

function CropHeatBody() {
  const { farm, cycleVersion, openCropDialog, notifyCycleChanged } = useRashkarShell();

  const [assessment, setAssessment] = useState<CropHeatAssessmentResponse | null>(null);
  const [history, setHistory] = useState<CropHeatHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedStage, setSelectedStage] = useState<string>("");
  const [confirmingStage, setConfirmingStage] = useState(false);
  const [stageMsg, setStageMsg] = useState<string | null>(null);
  const [stageErr, setStageErr] = useState<string | null>(null);

  const loadAssessment = useCallback(async () => {
    if (!farm?.id) return;
    setLoading(true);
    setError(null);
    try {
      const [res, hist] = await Promise.all([
        rashkarApi.assessCropHeat({ farm_id: farm.id }),
        rashkarApi.getCropHeatHistory(farm.id, 10).catch(() => []),
      ]);
      setAssessment(res);
      setHistory(hist);
    } catch (err: any) {
      setError(err?.message || "Failed to evaluate crop heat stress.");
    } finally {
      setLoading(false);
    }
  }, [farm?.id]);

  useEffect(() => {
    if (farm?.id) {
      loadAssessment();
    }
  }, [farm?.id, cycleVersion, loadAssessment]);

  useEffect(() => {
    if (!assessment?.supported_stages?.length) {
      setSelectedStage(assessment?.growth_stage_code || "");
      return;
    }
    const current = assessment.farmer_confirmed_stage || assessment.growth_stage_code || "";
    const matched = assessment.supported_stages.find(
      (s) =>
        s.stage_code.toLowerCase() === current.toLowerCase() ||
        current.toLowerCase().includes(s.stage_code.toLowerCase().replace("stage_", "")),
    );
    setSelectedStage(matched?.stage_code || assessment.supported_stages[0].stage_code);
  }, [
    assessment?.assessment_id,
    assessment?.growth_stage_code,
    assessment?.farmer_confirmed_stage,
  ]);

  const handleConfirmStage = async () => {
    if (!farm?.id || !selectedStage) return;
    setConfirmingStage(true);
    setStageMsg(null);
    setStageErr(null);
    try {
      await rashkarApi.confirmCropStage(farm.id, selectedStage);
      setStageMsg(`Stage confirmed as ${formatTokenLabel(selectedStage)}. Recalculated crop risk.`);
      notifyCycleChanged();
      await loadAssessment();
    } catch (err: any) {
      setStageErr(err?.message || "Failed to confirm crop growth stage.");
    } finally {
      setConfirmingStage(false);
    }
  };

  if (!farm) return null;

  if (loading && !assessment) {
    return (
      <Card>
        <CardContent className="py-12">
          <LoadingState label="Evaluating crop phenological heat stress..." />
        </CardContent>
      </Card>
    );
  }

  if (error && !assessment) {
    return (
      <Card>
        <CardContent className="py-6">
          <ErrorState
            title="Could not load crop heat assessment"
            description={error}
            action={
              <Button type="button" variant="secondary" onClick={loadAssessment}>
                <RefreshCw size={15} /> Try again
              </Button>
            }
          />
        </CardContent>
      </Card>
    );
  }

  if (!assessment) return null;

  // Honest NO_ACTIVE_CROP state
  if (
    assessment.status === "NO_ACTIVE_CROP" ||
    !assessment.has_active_crop ||
    assessment.needs_crop_registration
  ) {
    return (
      <Card>
        <CardContent className="py-8">
          <EmptyState
            icon={Sprout}
            title="No active crop registered for this farm"
            description={
              assessment.message ||
              "Register what is currently planted on your plot (and sowing date) so RASHKAR can check stage-specific ICAR-CRIDA heat limits without guessing a fallback crop."
            }
            action={
              <Button type="button" onClick={openCropDialog}>
                <Plus size={16} /> Register Active Crop
              </Button>
            }
          />
        </CardContent>
      </Card>
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
                <Badge variant="green">
                  {assessment.crop_common_name || formatCropLabel(assessment.crop_code)}
                </Badge>
              </div>
              <h2 className="text-lg font-extrabold text-ink">
                Crop heat forecast is currently unavailable
              </h2>
              <p className="text-sm leading-6 text-muted">
                {assessment.message ||
                  "Forecast weather data unavailable for this farm coordinate; crop heat assessment paused without synthetic fallback temperatures."}
              </p>
              <Button type="button" size="sm" variant="secondary" onClick={loadAssessment}>
                <RefreshCw size={14} /> Retry Weather Feed
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const overallTone = getRiskTone(assessment.overall_crop_heat_risk);
  const daytimeTone = getRiskTone(assessment.daytime_heat_stress_level);
  const interventions =
    assessment.recommended_interventions?.length > 0
      ? assessment.recommended_interventions
      : assessment.field_recommendations || [];
  const outlook = assessment.daily_outlook?.length
    ? assessment.daily_outlook
    : assessment.four_day_outlook || [];

  return (
    <div className="space-y-6">
      {/* Season Expiry Notice */}
      {assessment.is_season_expired && (
        <div className="flex flex-col gap-3 rounded-2xl border border-[#efb89c] bg-[#fff5ef] p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3 text-xs leading-5 text-[#9a3700] sm:text-sm">
            <CalendarClock size={19} className="mt-0.5 shrink-0" />
            <div>
              <strong>Season Status: {assessment.season_status}</strong> —{" "}
              {assessment.season_expiry_message ||
                "Sowing date exceeds typical season duration. Update your active crop cycle for valid stage-specific thresholds."}
            </div>
          </div>
          <Button type="button" size="sm" variant="accent" onClick={openCropDialog} className="shrink-0">
            Update Active Crop
          </Button>
        </div>
      )}

      {/* Active Crop Status Header + Inline Farmer Stage Confirmation */}
      <Card>
        <CardContent className="space-y-4 p-5 sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="green">
                  {assessment.crop_common_name || formatCropLabel(assessment.crop_code)}
                </Badge>
                {assessment.crop_variety && (
                  <Badge variant="neutral">Variety: {assessment.crop_variety}</Badge>
                )}
                {assessment.days_after_sowing != null && (
                  <Badge variant="outline">DAS {assessment.days_after_sowing} days</Badge>
                )}
                {assessment.irrigation_status && (
                  <Badge variant="outline">{assessment.irrigation_status}</Badge>
                )}
                <Badge variant={assessment.is_soil_synthetic ? "orange" : "neutral"}>
                  <Layers size={11} className="mr-1" />
                  {assessment.soil_provenance_label}
                </Badge>
              </div>

              <h2 className="text-lg font-extrabold text-ink sm:text-xl">
                Growth Stage: {assessment.growth_stage_name_en || "Unrecorded"}
                {assessment.growth_stage_name_mr ? (
                  <span className="ml-2 text-sm font-bold text-muted">
                    ({assessment.growth_stage_name_mr})
                  </span>
                ) : null}
              </h2>
              <p className="text-xs text-muted">
                Stage source: <strong>{formatTokenLabel(assessment.stage_source)}</strong>
                {assessment.sowing_date ? ` · Sown on ${assessment.sowing_date}` : ""}
                {assessment.crop_area_acres != null
                  ? ` · ${assessment.crop_area_acres.toFixed(2)} acres`
                  : ""}
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button type="button" size="sm" variant="secondary" onClick={loadAssessment} disabled={loading}>
                <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
              </Button>
            </div>
          </div>

          {/* Inline Farmer Stage Confirmation */}
          {assessment.supported_stages?.length > 0 && (
            <div className="rounded-2xl border border-line bg-canvas p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div className="flex-1 space-y-1">
                  <label className="block text-xs font-extrabold text-forest">
                    Confirm or Correct Field Growth Stage
                  </label>
                  <p className="text-[11px] text-muted">
                    If your field crop is ahead or behind the sowing-date estimate, select what you
                    observe in the field to lock exact critical heat thresholds.
                  </p>
                  <select
                    aria-label="Farmer Stage Confirmation"
                    value={selectedStage}
                    onChange={(e) => setSelectedStage(e.target.value)}
                    className="mt-1.5 min-h-10 w-full max-w-lg rounded-xl border border-line bg-white px-3 text-xs font-bold text-ink"
                  >
                    {assessment.supported_stages.map((st) => (
                      <option key={st.stage_code} value={st.stage_code}>
                        {st.stage_name_en || st.stage_name || formatTokenLabel(st.stage_code)}
                        {st.stage_name_mr ? ` (${st.stage_name_mr})` : ""}
                        {st.das_range ? ` · ${st.das_range}` : ""}
                        {st.crit_tmax != null ? ` · Crit ≥${st.crit_tmax}°C` : ""}
                      </option>
                    ))}
                  </select>
                </div>

                <Button
                  type="button"
                  size="sm"
                  disabled={!selectedStage || confirmingStage}
                  onClick={handleConfirmStage}
                  className="shrink-0"
                >
                  {confirmingStage ? (
                    <>
                      <LoaderCircle size={14} className="animate-spin" /> Confirming...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={14} /> Confirm Stage
                    </>
                  )}
                </Button>
              </div>
              {stageMsg && <p className="mt-2 text-xs font-bold text-forest">{stageMsg}</p>}
              {stageErr && <p className="mt-2 text-xs font-bold text-[#b71c1c]">{stageErr}</p>}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Overall Crop Heat Verdict */}
      <Card className={`border ${overallTone.surfaceClass}`}>
        <CardContent className="space-y-4 p-5 sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={overallTone.badgeVariant}>
                  OVERALL CROP HEAT RISK: {overallTone.label}
                </Badge>
                <Badge variant={daytimeTone.badgeVariant}>
                  DAYTIME STRESS: {daytimeTone.label}
                </Badge>
                {assessment.warm_night_respiration_hazard && (
                  <Badge variant="destructive">Warm Night Respiration Hazard</Badge>
                )}
              </div>

              <h3 className="text-lg font-extrabold text-ink sm:text-xl">
                {assessment.stage_biological_vulnerability || assessment.physiological_mechanism}
              </h3>

              {assessment.physiological_mechanism &&
                assessment.physiological_mechanism !== assessment.stage_biological_vulnerability && (
                  <p className="text-sm leading-6 text-ink/90">
                    {assessment.physiological_mechanism}
                  </p>
                )}
            </div>

            <div className="grid shrink-0 grid-cols-2 gap-2.5 sm:grid-cols-4 lg:grid-cols-2">
              <div className="rounded-xl border border-line/80 bg-white/90 px-3.5 py-2.5">
                <p className="text-[11px] font-bold text-muted">Peak Tmax / Limit</p>
                <p className="mt-0.5 text-base font-extrabold text-ink">
                  {assessment.tmax_forecast_c != null ? `${assessment.tmax_forecast_c.toFixed(1)}°C` : "—"}{" "}
                  <span className="text-xs font-semibold text-muted">
                    /{" "}
                    {assessment.critical_tmax_threshold_c != null
                      ? `${assessment.critical_tmax_threshold_c.toFixed(1)}°C`
                      : "—"}
                  </span>
                </p>
              </div>
              <div className="rounded-xl border border-line/80 bg-white/90 px-3.5 py-2.5">
                <p className="text-[11px] font-bold text-muted">Night Tmin / Limit</p>
                <p className="mt-0.5 text-base font-extrabold text-ink">
                  {assessment.tmin_forecast_c != null ? `${assessment.tmin_forecast_c.toFixed(1)}°C` : "—"}{" "}
                  <span className="text-xs font-semibold text-muted">
                    /{" "}
                    {assessment.critical_tmin_threshold_c != null
                      ? `${assessment.critical_tmin_threshold_c.toFixed(1)}°C`
                      : "—"}
                  </span>
                </p>
              </div>
              <div className="rounded-xl border border-line/80 bg-white/90 px-3.5 py-2.5">
                <p className="text-[11px] font-bold text-muted">Above Critical Hours</p>
                <p className="mt-0.5 text-base font-extrabold text-ink">
                  {assessment.hours_above_critical != null
                    ? `${assessment.hours_above_critical.toFixed(1)} hrs`
                    : "—"}
                </p>
              </div>
              <div className="rounded-xl border border-line/80 bg-white/90 px-3.5 py-2.5">
                <p className="text-[11px] font-bold text-muted">Hot Days in Outlook</p>
                <p className="mt-0.5 text-base font-extrabold text-ink">
                  {assessment.consecutive_hot_days != null
                    ? `${assessment.consecutive_hot_days} / 4 days`
                    : "—"}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 4-Day Daily Outlook Grid */}
      {outlook.length > 0 && (
        <section aria-label="4-day crop heat outlook">
          <SectionHeader
            title="4-Day Daily Heat Outlook"
            description="Daytime peak (Tmax), night minimum (Tmin), and hours exceeding your crop stage critical temperature."
          />
          <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
            {outlook.map((day, idx) => {
              const dayTone = getRiskTone(day.risk_category);
              return (
                <Card key={`${day.day_label}-${idx}`}>
                  <CardContent className="space-y-3 p-4 sm:p-5">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-extrabold text-ink">{day.day_label}</p>
                        <p className="text-[11px] text-muted">{day.date}</p>
                      </div>
                      <Badge variant={dayTone.badgeVariant}>{dayTone.label}</Badge>
                    </div>

                    <div className="grid grid-cols-3 gap-2 rounded-xl bg-canvas p-2.5 text-center">
                      <div>
                        <p className="text-[10px] font-bold text-muted">Tmax</p>
                        <p className="text-sm font-extrabold text-accent">
                          {day.tmax_c.toFixed(1)}°C
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] font-bold text-muted">Tmin</p>
                        <p className="text-sm font-extrabold text-calm">
                          {day.tmin_c.toFixed(1)}°C
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] font-bold text-muted">Exceed</p>
                        <p className="text-sm font-extrabold text-ink">
                          {day.hours_above_critical.toFixed(1)}h
                        </p>
                      </div>
                    </div>

                    <p className="text-xs leading-5 text-muted">{day.explanation}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>
      )}

      {/* Bilingual English + Marathi Field Interventions */}
      <section aria-label="Bilingual field interventions">
        <SectionHeader
          title="Recommended Field Interventions (English & मराठी)"
          description="Practical protective actions tailored to your crop stage and irrigation setup."
        />
        {interventions.length === 0 ? (
          <Card>
            <CardContent className="py-6 text-xs text-muted">
              No stage-specific interventions generated (for example, if the registered crop season
              has expired). Update your active crop cycle above to get active recommendations.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {interventions.map((inv) => (
              <Card key={inv.intervention_id}>
                <CardContent className="space-y-3 p-5">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="space-y-1">
                      <h4 className="text-base font-extrabold text-ink">{inv.title_en}</h4>
                      <p className="text-sm font-bold text-forest">{inv.title_mr}</p>
                    </div>
                    <Badge variant="green">{formatTokenLabel(inv.category)}</Badge>
                  </div>

                  <p className="text-xs leading-5 text-ink/90">{inv.description_en}</p>
                  <div className="rounded-xl border border-[#dce8dc] bg-[#f4faf4] p-3 text-xs leading-5 text-forest">
                    <strong>मराठी सूचना:</strong> {inv.description_mr}
                  </div>

                  <p className="text-xs leading-5 text-muted">
                    <strong className="text-ink">Why this helps:</strong> {inv.why_appropriate}
                  </p>

                  <div className="grid gap-2 rounded-xl bg-canvas p-3 text-[11px] sm:grid-cols-2">
                    {inv.application_dose && (
                      <div>
                        <span className="font-bold text-muted">Dose / Schedule:</span>
                        <p className="font-semibold text-ink">{inv.application_dose}</p>
                      </div>
                    )}
                    {inv.application_method && (
                      <div>
                        <span className="font-bold text-muted">Method:</span>
                        <p className="font-semibold text-ink">{inv.application_method}</p>
                      </div>
                    )}
                    {inv.infrastructure_requirements && (
                      <div>
                        <span className="font-bold text-muted">Equipment:</span>
                        <p className="font-semibold text-ink">{inv.infrastructure_requirements}</p>
                      </div>
                    )}
                    {inv.trigger_condition && (
                      <div>
                        <span className="font-bold text-muted">Trigger:</span>
                        <p className="font-semibold text-ink">{inv.trigger_condition}</p>
                      </div>
                    )}
                  </div>

                  <p className="text-[11px] text-muted">
                    <ShieldCheck size={12} className="mr-1 inline text-leaf" />
                    <strong>Evidence:</strong> {inv.evidence_citation}
                    {inv.source_page_or_table ? ` (${inv.source_page_or_table})` : ""}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Collapsible More Details */}
      <MoreDetailsPanel
        title="More Scientific Details — VPD, GDD, Night Respiration & Citations"
        subtitle="Critical stage thresholds, vapor pressure deficit, personalized vulnerability score, and ICAR-CRIDA / SAU sources."
        badgeText="ICAR-CRIDA / SAU"
      >
        <div className="space-y-4 text-xs">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-line bg-white p-3.5">
              <p className="font-bold text-muted">Critical Tmax Threshold</p>
              <p className="mt-1 text-base font-extrabold text-ink">
                {assessment.critical_tmax_threshold_c != null
                  ? `${assessment.critical_tmax_threshold_c.toFixed(1)}°C`
                  : "—"}
              </p>
              <p className="mt-0.5 text-[11px] text-muted">
                Optimal:{" "}
                {assessment.optimal_temp_min_c != null && assessment.optimal_temp_max_c != null
                  ? `${assessment.optimal_temp_min_c}–${assessment.optimal_temp_max_c}°C`
                  : "—"}
              </p>
            </div>

            <div className="rounded-xl border border-line bg-white p-3.5">
              <p className="font-bold text-muted">Peak VPD</p>
              <p className="mt-1 text-base font-extrabold text-ink">
                {assessment.peak_vpd_kpa != null
                  ? `${assessment.peak_vpd_kpa.toFixed(2)} kPa`
                  : "Unavailable"}
              </p>
              <p className="mt-0.5 text-[11px] text-muted">Atmospheric evaporative pull</p>
            </div>

            <div className="rounded-xl border border-line bg-white p-3.5">
              <p className="font-bold text-muted">Warm Night Hazard</p>
              <p className="mt-1 flex items-center gap-1.5 text-base font-extrabold text-ink">
                <Moon size={15} className="text-calm" />
                {assessment.warm_night_respiration_hazard ? "Active" : "Normal"}
              </p>
              <p className="mt-0.5 text-[11px] text-muted">
                Penalty score:{" "}
                {assessment.warm_night_penalty_score != null
                  ? assessment.warm_night_penalty_score.toFixed(2)
                  : "0.00"}
              </p>
            </div>

            <div className="rounded-xl border border-line bg-white p-3.5">
              <p className="font-bold text-muted">Cumulative GDD</p>
              <p className="mt-1 flex items-center gap-1.5 text-base font-extrabold text-ink">
                <Thermometer size={15} className="text-accent" />
                {assessment.cumulative_heat_units_gdd != null
                  ? `${assessment.cumulative_heat_units_gdd.toFixed(1)} °C-d`
                  : "—"}
              </p>
              <p className="mt-0.5 text-[11px] text-muted">
                Base temp:{" "}
                {assessment.base_temp_c != null ? `${assessment.base_temp_c}°C` : "—"}
              </p>
            </div>
          </div>

          {assessment.personalized_crop_vulnerability_score && (
            <div className="rounded-xl border border-line bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-extrabold text-ink">
                  Personalized Crop Vulnerability Score:{" "}
                  {assessment.personalized_crop_vulnerability_score.score_0_100}/100
                </p>
                <Badge variant="neutral">
                  {formatTokenLabel(
                    assessment.personalized_crop_vulnerability_score.vulnerability_level,
                  )}
                </Badge>
              </div>
              {assessment.personalized_crop_vulnerability_score.action_recommendation && (
                <p className="mt-1.5 text-muted">
                  {assessment.personalized_crop_vulnerability_score.action_recommendation}
                </p>
              )}
              {assessment.personalized_crop_vulnerability_score.sub_indices && (
                <div className="mt-3 grid gap-2 sm:grid-cols-3">
                  {Object.entries(
                    assessment.personalized_crop_vulnerability_score.sub_indices,
                  ).map(([k, v]) => (
                    <div key={k} className="rounded-lg bg-canvas px-3 py-2">
                      <span className="block text-[10px] text-muted">{formatTokenLabel(k)}</span>
                      <span className="font-bold text-ink">{v} pts</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="space-y-1.5 rounded-xl border border-line bg-white p-4 text-muted">
            <p>
              <strong className="text-ink">ICAR-CRIDA / SAU Citation:</strong>{" "}
              {assessment.evidence_citation || assessment.institution_attribution}
            </p>
            {assessment.topographic_downscaling && (
              <p>
                <strong className="text-ink">Topographic Downscaling:</strong>{" "}
                {assessment.topographic_downscaling.methodology} (
                {formatTokenLabel(String(assessment.topographic_downscaling.status || ""))})
              </p>
            )}
          </div>
        </div>
      </MoreDetailsPanel>

      {/* Farm Crop Heat History */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History size={17} className="text-leaf" /> Crop Heat Assessment History
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-3">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] text-left text-xs">
                <thead>
                  <tr className="border-b border-line text-[11px] font-extrabold uppercase tracking-wider text-muted">
                    <th className="py-2 pr-3">Assessed (IST)</th>
                    <th className="py-2 pr-3">Crop</th>
                    <th className="py-2 pr-3">Stage</th>
                    <th className="py-2 pr-3">Peak Tmax</th>
                    <th className="py-2 pr-3">Stress Score</th>
                    <th className="py-2">Tier</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/60">
                  {history.map((row) => {
                    const tone = getRiskTone(row.stress_tier);
                    return (
                      <tr key={row.id}>
                        <td className="py-2.5 pr-3 font-semibold text-ink">
                          {row.assessed_at_ist}
                        </td>
                        <td className="py-2.5 pr-3 font-bold text-ink">
                          {formatCropLabel(row.crop_code)}
                        </td>
                        <td className="py-2.5 pr-3 text-muted">
                          {formatTokenLabel(row.stage_code)}
                        </td>
                        <td className="py-2.5 pr-3 text-ink">
                          {row.peak_tmax_c != null ? `${row.peak_tmax_c.toFixed(1)}°C` : "—"}
                        </td>
                        <td className="py-2.5 pr-3 text-muted">
                          {row.overall_stress_score != null
                            ? `${row.overall_stress_score.toFixed(1)} / 100`
                            : "—"}
                        </td>
                        <td className="py-2.5">
                          <Badge variant={tone.badgeVariant}>{tone.label}</Badge>
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

export function CropHeatScreen() {
  return (
    <RashkarShell
      activeTab="crop-heat"
      eyebrow="RASHKAR · Crop Heat Stress"
      title="Will the heat affect my crop?"
      description="Stage-specific daytime and warm-night thermal risk screening with bilingual English + Marathi field interventions."
    >
      <CropHeatBody />
    </RashkarShell>
  );
}
