"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  CircleDollarSign,
  CloudOff,
  CloudSun,
  Flame,
  Layers,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  Sprout,
  ThermometerSun,
} from "lucide-react";
import Link from "next/link";
import { ErrorState, LoadingState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionHeader } from "@/components/section-header";
import { rashkarApi } from "../lib/api";
import { formatCropLabel, formatTokenLabel, getRiskTone } from "../lib/format";
import type { RashkarCanonicalCropItem } from "../types";
import { RashkarShell, useRashkarShell } from "./RashkarShell";

function OverviewBody() {
  const {
    farm,
    overview,
    overviewLoading,
    overviewError,
    openCropDialog,
    refreshOverview,
    notifyCycleChanged,
  } = useRashkarShell();

  const [cropsWithStages, setCropsWithStages] = useState<RashkarCanonicalCropItem[]>([]);
  const [stageConfirmOpen, setStageConfirmOpen] = useState(false);
  const [selectedStageCode, setSelectedStageCode] = useState("");
  const [confirmingStage, setConfirmingStage] = useState(false);
  const [stageMsg, setStageMsg] = useState<string | null>(null);
  const [stageErr, setStageErr] = useState<string | null>(null);

  const activeCycle = overview?.active_crop_cycle ?? null;

  useEffect(() => {
    let mounted = true;
    rashkarApi
      .listCrops(true)
      .then((list) => {
        if (mounted) setCropsWithStages(list);
      })
      .catch(() => {
        // Non-fatal; fallback stage list remains empty until retried
      });
    return () => {
      mounted = false;
    };
  }, []);

  const activeCropMeta = useMemo(() => {
    if (!activeCycle) return undefined;
    return cropsWithStages.find((c) => c.crop_code === activeCycle.crop_code);
  }, [cropsWithStages, activeCycle]);

  useEffect(() => {
    if (activeCycle?.current_stage_code) {
      setSelectedStageCode(activeCycle.current_stage_code);
    } else if (activeCropMeta?.stages?.length) {
      setSelectedStageCode(activeCropMeta.stages[0].stage_code);
    } else {
      setSelectedStageCode("");
    }
  }, [activeCycle?.id, activeCycle?.current_stage_code, activeCropMeta]);

  const handleConfirmStage = async () => {
    if (!farm?.id || !selectedStageCode) return;
    setConfirmingStage(true);
    setStageErr(null);
    setStageMsg(null);
    try {
      await rashkarApi.confirmCropStage(farm.id, selectedStageCode, activeCycle?.id);
      setStageMsg(`Confirmed stage: ${formatTokenLabel(selectedStageCode)}.`);
      setStageConfirmOpen(false);
      notifyCycleChanged();
    } catch (err: any) {
      setStageErr(err?.message || "Failed to confirm growth stage.");
    } finally {
      setConfirmingStage(false);
    }
  };

  if (!farm) return null;

  if (overviewLoading && !overview) {
    return (
      <Card>
        <CardContent className="py-12">
          <LoadingState label="Checking weather, soil, and active crop readiness..." />
        </CardContent>
      </Card>
    );
  }

  if (overviewError && !overview) {
    return (
      <Card>
        <CardContent className="py-6">
          <ErrorState
            title="Could not load RASHKAR overview"
            description={overviewError}
            action={
              <Button type="button" variant="secondary" onClick={refreshOverview}>
                <RefreshCw size={15} /> Try again
              </Button>
            }
          />
        </CardContent>
      </Card>
    );
  }

  if (!overview) return null;

  const wx = overview.weather;
  const wxOk = wx?.status === "OK";
  const soil = overview.soil;
  const latestWorker = overview.latest_assessments.worker_heat;
  const latestCropHeat = overview.latest_assessments.crop_heat;
  const latestYield = overview.latest_assessments.yield_intelligence;

  const soilTierLabel = soil?.is_lab_measured
    ? "Lab Tested (Verified)"
    : soil?.data_provenance
      ? soil.is_synthetic
        ? "Map / Modelled Estimate"
        : "Spatial Soil Profile"
      : "Unsampled / Unavailable";

  const soilBadgeVariant = soil?.is_lab_measured
    ? "green"
    : soil?.data_provenance
      ? "orange"
      : "neutral";

  const entryCards = [
    {
      key: "worker-heat",
      title: "Can I work outside now?",
      subtitle: "Worker Heat & WBGT Safety",
      href: "/rashkar/worker-heat",
      icon: ThermometerSun,
      iconTone: "bg-[#fff1e8] text-accent",
      description:
        "Check 0–6 hour wet-bulb globe temperature (WBGT), work-rest limits, hydration guidance, and emergency heat triage.",
      badge: latestWorker ? (
        <Badge variant={getRiskTone(latestWorker.risk_tier).badgeVariant}>
          {getRiskTone(latestWorker.risk_tier).label} · {latestWorker.calculated_wbgt_c.toFixed(1)}°C WBGT
        </Badge>
      ) : (
        <Badge variant="neutral">Not assessed yet</Badge>
      ),
      footerText: latestWorker
        ? `Last checked ${latestWorker.assessed_at_ist}`
        : "Run 0–6h field safety check",
    },
    {
      key: "crop-heat",
      title: "Will the heat affect my crop?",
      subtitle: "Crop Phenology Heat Stress",
      href: "/rashkar/crop-heat",
      icon: Flame,
      iconTone: "bg-[#fdeeee] text-[#c62828]",
      description:
        "Stage-specific thermal thresholds, warm-night respiration check, 4-day outlook, and bilingual English + Marathi field actions.",
      badge: latestCropHeat ? (
        <Badge variant={getRiskTone(latestCropHeat.stress_tier).badgeVariant}>
          {getRiskTone(latestCropHeat.stress_tier).label} ·{" "}
          {formatCropLabel(latestCropHeat.crop_code)}
        </Badge>
      ) : overview.has_active_crop ? (
        <Badge variant="neutral">Ready to check</Badge>
      ) : (
        <Badge variant="orange">Needs active crop</Badge>
      ),
      footerText: latestCropHeat
        ? `Last checked ${latestCropHeat.assessed_at_ist}`
        : overview.has_active_crop
          ? "Assess 4-day crop thermal risk"
          : "Register crop to unlock stage thresholds",
    },
    {
      key: "yield",
      title: "What risk does my crop yield face?",
      subtitle: "Yield Intelligence & APY Baselines",
      href: "/rashkar/yield",
      icon: BarChart3,
      iconTone: "bg-[#e8f5e9] text-forest",
      description:
        "Official DES APY historical district yields (1997–2021 P10–P90), 5-dimension stress screening, and soil suitability.",
      badge: latestYield ? (
        <Badge variant={getRiskTone(latestYield.composite_risk_tier).badgeVariant}>
          {getRiskTone(latestYield.composite_risk_tier).label} RISK ·{" "}
          {formatCropLabel(latestYield.crop_code)}
        </Badge>
      ) : (
        <Badge variant="neutral">Pre-sowing or active</Badge>
      ),
      footerText: latestYield
        ? `Last screened ${latestYield.assessed_at_ist}`
        : "View district benchmarks & stress risks",
    },
    {
      key: "earn-more",
      title: "What extra income can my farm earn?",
      subtitle: "Earn More & 12-Month Simulator",
      href: "/rashkar/earn-more",
      icon: CircleDollarSign,
      iconTone: "bg-[#e7f1fa] text-calm",
      description:
        "Discover ₹0 zero-cash cost savers and low-investment enterprises matched to your land, water, labor, and saved farm plans.",
      badge: (
        <Badge variant={overview.saved_income_plans_count > 0 ? "green" : "neutral"}>
          {overview.saved_income_plans_count} saved{" "}
          {overview.saved_income_plans_count === 1 ? "plan" : "plans"}
        </Badge>
      ),
      footerText: "Explore opportunities & run 12-month cash flow",
    },
  ];

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Honesty / Scientific Integrity Strip */}
      <div className="flex flex-col gap-3 rounded-2xl border border-[#cde0ce] bg-[#f1f8f1] p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3 text-sm text-forest">
          <ShieldCheck size={19} className="mt-0.5 shrink-0" />
          <p className="text-xs leading-5 sm:text-sm">
            <strong>Verified Field Context Only:</strong> RASHKAR uses live Open-Meteo weather,
            your registered crop cycle, measured or clearly labeled soil records, and official DES
            APY benchmarks — never hidden demo crops or fabricated yields.
          </p>
        </div>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          onClick={refreshOverview}
          disabled={overviewLoading}
          className="shrink-0"
        >
          <RefreshCw size={14} className={overviewLoading ? "animate-spin" : ""} />
          Refresh Live Feed
        </Button>
      </div>

      {/* Plain-Language Farm Readiness Strip */}
      <section aria-label="Farm readiness overview">
        <SectionHeader
          title="Farm Readiness Strip"
          description="Live status of your crop registration, Open-Meteo weather feed, soil tier, and saved income plans."
          action={
            <div className="flex flex-wrap gap-2">
              <Button type="button" size="sm" variant="secondary" onClick={openCropDialog}>
                <Sprout size={14} />
                {overview.has_active_crop ? "Register / Switch Active Crop" : "Register Active Crop"}
              </Button>
              {overview.has_active_crop && (
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => setStageConfirmOpen((v) => !v)}
                >
                  <CheckCircle2 size={14} /> Confirm Growth Stage
                </Button>
              )}
            </div>
          }
        />

        {stageMsg && (
          <div className="mb-4 rounded-xl border border-[#c8e6c9] bg-[#eef7ee] px-4 py-2.5 text-xs font-bold text-forest">
            {stageMsg}
          </div>
        )}
        {stageErr && (
          <div className="mb-4 rounded-xl border border-[#f2b8b5] bg-[#fdeeee] px-4 py-2.5 text-xs font-bold text-[#b71c1c]">
            {stageErr}
          </div>
        )}

        {stageConfirmOpen && overview.has_active_crop && (
          <Card className="mb-4 border-[#b8d0ba] bg-[#f8fbf8]">
            <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-end sm:justify-between">
              <div className="flex-1 space-y-1.5">
                <p className="text-xs font-extrabold text-forest">
                  Confirm Current Growth Stage for{" "}
                  {activeCropMeta?.common_name_en || formatCropLabel(activeCycle?.crop_code)}
                </p>
                {activeCropMeta?.stages?.length ? (
                  <select
                    aria-label="Confirm Growth Stage"
                    value={selectedStageCode}
                    onChange={(e) => setSelectedStageCode(e.target.value)}
                    className="min-h-10 w-full max-w-md rounded-xl border border-line bg-white px-3 text-xs font-bold text-ink"
                  >
                    {activeCropMeta.stages.map((st) => (
                      <option key={st.stage_code} value={st.stage_code}>
                        {st.stage_name_en}
                        {st.stage_name_mr ? ` (${st.stage_name_mr})` : ""}
                        {st.typical_das_start != null && st.typical_das_end != null
                          ? ` — DAS ${st.typical_das_start}–${st.typical_das_end}`
                          : ""}
                      </option>
                    ))}
                  </select>
                ) : (
                  <p className="text-xs text-muted">
                    Detailed stage list is unavailable for this crop; open Crop Heat to inspect or
                    register with sowing date.
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => setStageConfirmOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="button"
                  size="sm"
                  disabled={!selectedStageCode || confirmingStage}
                  onClick={handleConfirmStage}
                >
                  {confirmingStage ? (
                    <>
                      <LoaderCircle size={14} className="animate-spin" /> Saving...
                    </>
                  ) : (
                    "Save Confirmed Stage"
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {/* 1. Active Crop Readiness */}
          <Card>
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs font-bold text-muted">Active Crop Cycle</p>
                <span className="grid size-9 place-items-center rounded-xl bg-[#edf5ed] text-leaf">
                  <Sprout size={18} />
                </span>
              </div>
              {activeCycle ? (
                <>
                  <p className="mt-2 text-lg font-extrabold text-ink">
                    {activeCropMeta?.common_name_en || formatCropLabel(activeCycle.crop_code)}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {activeCycle.variety_name && (
                      <Badge variant="neutral">{activeCycle.variety_name}</Badge>
                    )}
                    <Badge variant="green">
                      {activeCycle.current_stage_code
                        ? formatTokenLabel(activeCycle.current_stage_code)
                        : "Stage estimated by DAS"}
                    </Badge>
                  </div>
                  <p className="mt-2.5 text-[11px] leading-4 text-muted">
                    {activeCycle.sowing_date
                      ? `Sown ${activeCycle.sowing_date}`
                      : "No sowing date recorded"}
                    {activeCycle.season ? ` · ${formatTokenLabel(activeCycle.season)}` : ""}
                  </p>
                </>
              ) : (
                <>
                  <p className="mt-2 text-base font-extrabold text-accent">
                    No active crop registered
                  </p>
                  <p className="mt-1.5 text-xs leading-5 text-muted">
                    Register your standing crop to unlock stage-specific heat alerts and yield
                    screening.
                  </p>
                  <Button
                    type="button"
                    size="sm"
                    variant="primary"
                    className="mt-3 w-full"
                    onClick={openCropDialog}
                  >
                    Register Crop
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          {/* 2. Live Open-Meteo Weather */}
          <Card>
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs font-bold text-muted">Live Weather Feed</p>
                <span
                  className={`grid size-9 place-items-center rounded-xl ${
                    wxOk ? "bg-[#e7f1fa] text-calm" : "bg-[#f3f5f3] text-muted"
                  }`}
                >
                  {wxOk ? <CloudSun size={18} /> : <CloudOff size={18} />}
                </span>
              </div>
              {wxOk ? (
                <>
                  <p className="mt-2 text-lg font-extrabold text-ink">
                    {wx.current_air_temp_c != null ? `${wx.current_air_temp_c.toFixed(1)}°C` : "—"}
                    <span className="ml-2 text-xs font-bold text-muted">
                      RH{" "}
                      {wx.current_relative_humidity_pct != null
                        ? `${wx.current_relative_humidity_pct.toFixed(0)}%`
                        : "—"}
                    </span>
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] font-semibold text-ink">
                    {wx.current_wind_speed_ms != null && (
                      <Badge variant="outline">
                        Wind {(wx.current_wind_speed_ms * 3.6).toFixed(1)} km/h
                      </Badge>
                    )}
                    {wx.current_solar_irradiance_wm2 != null && (
                      <Badge variant="outline">
                        Solar {Math.round(wx.current_solar_irradiance_wm2)} W/m²
                      </Badge>
                    )}
                  </div>
                  <p className="mt-2.5 text-[11px] leading-4 text-muted">
                    {wx.provider || "Open-Meteo"} · {wx.timestamp_ist || "Live"}
                  </p>
                </>
              ) : (
                <>
                  <p className="mt-2 text-base font-extrabold text-muted">
                    Weather feed unavailable
                  </p>
                  <p className="mt-1.5 text-xs leading-5 text-muted">
                    {wx?.error || "Open-Meteo live feed could not be reached. No synthetic weather values generated."}
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          {/* 3. Soil Data Source / Tier */}
          <Card>
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs font-bold text-muted">Soil Data Tier</p>
                <span className="grid size-9 place-items-center rounded-xl bg-[#f5efe9] text-soil">
                  <Layers size={18} />
                </span>
              </div>
              <div className="mt-2">
                <Badge variant={soilBadgeVariant}>{soilTierLabel}</Badge>
              </div>
              <p className="mt-2 text-sm font-extrabold text-ink">
                {soil?.soil_texture ||
                  (soil?.soil_ph != null ? `pH ${soil.soil_ph.toFixed(1)}` : "Unsampled plot")}
              </p>
              <p className="mt-1.5 text-[11px] leading-4 text-muted">
                {soil?.soil_ph != null ? `pH ${soil.soil_ph.toFixed(1)}` : "pH not measured"}
                {soil?.organic_carbon_pct != null
                  ? ` · OC ${soil.organic_carbon_pct.toFixed(2)}%`
                  : ""}
              </p>
              <p className="mt-1 text-[11px] leading-4 text-muted">
                {soil?.data_provenance || "Soil data unavailable (unsampled coordinate)"}
              </p>
            </CardContent>
          </Card>

          {/* 4. Saved Income Plans */}
          <Card>
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs font-bold text-muted">Extra Income Plans</p>
                <span className="grid size-9 place-items-center rounded-xl bg-[#e7f1fa] text-calm">
                  <CircleDollarSign size={18} />
                </span>
              </div>
              <p className="mt-2 text-lg font-extrabold text-ink">
                {overview.saved_income_plans_count}{" "}
                <span className="text-xs font-bold text-muted">
                  saved {overview.saved_income_plans_count === 1 ? "plan" : "plans"}
                </span>
              </p>
              <p className="mt-1.5 text-xs leading-5 text-muted">
                Includes zero-cash cost savers and 12-month enterprise cash-flow scenarios.
              </p>
              <Link
                href="/rashkar/earn-more"
                className="mt-3 inline-flex items-center gap-1.5 text-xs font-extrabold text-forest hover:underline"
              >
                Open Earn More <ArrowRight size={14} />
              </Link>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* 4 Rich Decision Cards */}
      <section aria-label="RASHKAR advisory modules">
        <SectionHeader
          title="Ask RASHKAR About Your Farm"
          description="Four focused decision workspaces built around real farmer questions."
        />
        <div className="grid gap-4 sm:grid-cols-2">
          {entryCards.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.key}
                href={item.href}
                className="group flex flex-col justify-between rounded-card border border-line bg-white p-5 shadow-[0_12px_35px_rgba(27,65,32,.055)] transition hover:-translate-y-0.5 hover:border-[#b8d0ba] sm:p-6"
              >
                <div>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <span
                      className={`grid size-11 shrink-0 place-items-center rounded-2xl ${item.iconTone}`}
                    >
                      <Icon size={21} />
                    </span>
                    {item.badge}
                  </div>
                  <p className="mt-4 text-[11px] font-extrabold uppercase tracking-[0.12em] text-muted">
                    {item.subtitle}
                  </p>
                  <h3 className="mt-1 text-lg font-extrabold tracking-[-0.025em] text-ink">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-muted">{item.description}</p>
                </div>

                <div className="mt-5 flex items-center justify-between border-t border-line/70 pt-3.5 text-xs font-extrabold text-forest">
                  <span className="text-muted font-semibold">{item.footerText}</span>
                  <span className="inline-flex items-center gap-1.5 text-forest group-hover:translate-x-0.5 transition-transform">
                    Open <ArrowRight size={15} />
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}

export function OverviewScreen() {
  return (
    <RashkarShell
      activeTab="overview"
      eyebrow="RASHKAR · Decision Overview"
      title="Farm Readiness & Daily Decisions"
      description="Check field worker heat safety, crop stage heat stress, DES APY yield risk screening, and extra farm income options in plain language."
    >
      <OverviewBody />
    </RashkarShell>
  );
}
