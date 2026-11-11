"use client";

import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  CloudSun,
  Droplets,
  Flame,
  HeartPulse,
  Info,
  Loader2,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sun,
  UserCheck,
  Wheat,
  Wind,
} from "lucide-react";
import { useFarm } from "@/lib/farm-context";
import { heatRiskApi } from "@/lib/api/client";
import type {
  HeatRiskCrop,
  FarmHeatRiskResponse,
  CropHeatResponse,
  WorkerHeatResponse,
} from "@/lib/api/types";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";

export default function HeatRiskPage() {
  const { selectedFarm, farms, selectedFarmId } = useFarm();
  const [activeTab, setActiveTab] = useState("farm");

  // Supported crops
  const [crops, setCrops] = useState<HeatRiskCrop[]>([]);
  const [loadingCrops, setLoadingCrops] = useState(true);

  // Farm Heat Assessment state
  const [farmCropCode, setFarmCropCode] = useState<string>("soybean");
  const [farmAssessment, setFarmAssessment] = useState<FarmHeatRiskResponse | null>(null);
  const [loadingFarmAssessment, setLoadingFarmAssessment] = useState(false);
  const [farmError, setFarmError] = useState<string | null>(null);

  // Manual Crop Assessment state
  const [manualCropCode, setManualCropCode] = useState<string>("wheat");
  const [manualStage, setManualStage] = useState<string>("stage_flowering");
  const [manualTmax, setManualTmax] = useState<string>("35.0");
  const [manualTmin, setManualTmin] = useState<string>("21.0");
  const [cropAssessment, setCropAssessment] = useState<CropHeatResponse | null>(null);
  const [loadingCropAssessment, setLoadingCropAssessment] = useState(false);
  const [cropError, setCropError] = useState<string | null>(null);

  // Worker WBGT Assessment state
  const [workerTemp, setWorkerTemp] = useState<string>("36.0");
  const [workerHumidity, setWorkerHumidity] = useState<string>("55.0");
  const [workerWorkload, setWorkerWorkload] = useState<string>("moderate");
  const [workerClothing, setWorkerClothing] = useState<string>("standard_work_clothes");
  const [workerAssessment, setWorkerAssessment] = useState<WorkerHeatResponse | null>(null);
  const [loadingWorkerAssessment, setLoadingWorkerAssessment] = useState(false);
  const [workerError, setWorkerError] = useState<string | null>(null);

  // Fetch supported crops
  useEffect(() => {
    async function fetchCrops() {
      try {
        const res = await heatRiskApi.getCrops();
        setCrops(res.crops || []);
        if (res.crops?.length > 0) {
          setFarmCropCode(res.crops[0].crop_code);
          setManualCropCode(res.crops[0].crop_code);
        }
      } catch (err) {
        console.error("Failed to load heat risk crops:", err);
      } finally {
        setLoadingCrops(false);
      }
    }
    fetchCrops();
  }, []);

  // Run farm assessment whenever selected farm or chosen crop changes
  const runFarmAssessment = async () => {
    const farmId = selectedFarmId || farms[0]?.id;
    if (!farmId || !farmCropCode) return;
    setLoadingFarmAssessment(true);
    setFarmError(null);
    try {
      const res = await heatRiskApi.assessFarm(farmId, { crop_code: farmCropCode });
      setFarmAssessment(res);
    } catch (err: any) {
      setFarmError(err?.message || "Failed to calculate farm heat risk. Verify weather forecast availability.");
    } finally {
      setLoadingFarmAssessment(false);
    }
  };

  useEffect(() => {
    if (selectedFarmId || farms[0]?.id) {
      runFarmAssessment();
    }
  }, [selectedFarmId, farmCropCode, farms]);

  // Run Manual Crop Assessment
  const runCropAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingCropAssessment(true);
    setCropError(null);
    try {
      const res = await heatRiskApi.assessCrop({
        crop_code: manualCropCode,
        forecast_tmax_c: parseFloat(manualTmax),
        forecast_tmin_c: parseFloat(manualTmin),
        growth_stage: manualStage || undefined,
      });
      setCropAssessment(res);
    } catch (err: any) {
      setCropError(err?.message || "Failed to compute manual crop heat risk.");
    } finally {
      setLoadingCropAssessment(false);
    }
  };

  // Run Worker Assessment
  const runWorkerAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingWorkerAssessment(true);
    setWorkerError(null);
    try {
      const res = await heatRiskApi.assessWorker({
        air_temp_c: parseFloat(workerTemp),
        relative_humidity_pct: parseFloat(workerHumidity),
        workload_category: workerWorkload,
        clothing_type: workerClothing,
      });
      setWorkerAssessment(res);
    } catch (err: any) {
      setWorkerError(err?.message || "Failed to compute worker heat stress.");
    } finally {
      setLoadingWorkerAssessment(false);
    }
  };

  const selectedCropObj = crops.find((c) => c.crop_code === manualCropCode);

  const getRiskColor = (risk?: string) => {
    switch (risk?.toUpperCase()) {
      case "LOW":
        return "bg-forest/10 text-forest border-forest/30";
      case "MODERATE":
        return "bg-amber-500/10 text-amber-700 border-amber-500/30";
      case "HIGH":
      case "CRITICAL":
      case "SEVERE":
      case "EXTREME":
        return "bg-destructive/10 text-destructive border-destructive/30";
      default:
        return "bg-secondary text-foreground border-line";
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      <PageHeader
        eyebrow="Climate resilience"
        title="Heat Risk Intelligence"
        description="Forecast-linked crop thermal stress evaluations (ICAR-CRIDA phenology) and wet-bulb globe temperature (ISO 7243 / ACGIH) worker safety."
        backHref="/"
      />

      {/* Scientific Integrity Banner */}
      <div className="flex gap-3 rounded-2xl border border-[#cde0ce] bg-[#f1f8f1] p-4 text-sm text-forest">
        <Info className="mt-0.5 shrink-0" size={19} />
        <div className="text-xs leading-5 sm:text-sm">
          <strong>Deterministic Agronomic Modeling:</strong> Thermal risk thresholds are derived from peer-reviewed ICAR-CRIDA and State Agricultural Universities (SAU) crop-stage experiments. High night temperatures trigger dark respiration penalties.
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="farm" className="gap-1.5 text-xs sm:text-sm">
            <CloudSun size={15} /> Farm Forecast
          </TabsTrigger>
          <TabsTrigger value="crop" className="gap-1.5 text-xs sm:text-sm">
            <Wheat size={15} /> Crop Calculator
          </TabsTrigger>
          <TabsTrigger value="worker" className="gap-1.5 text-xs sm:text-sm">
            <HeartPulse size={15} /> Worker WBGT
          </TabsTrigger>
        </TabsList>

        {/* ── TAB 1: Farm Forecast Linked Heat Risk ─────────────────────── */}
        <TabsContent value="farm" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4">
              <div>
                <CardTitle className="text-base font-semibold">
                  Farm Heat Evaluation: {selectedFarm?.name || "Selected Parcel"}
                </CardTitle>
                <p className="text-xs text-muted">
                  5-day OpenWeather forecast correlated against verified phenological thresholds.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-muted">Crop:</span>
                <select
                  aria-label="Select Farm Crop"
                  value={farmCropCode}
                  onChange={(e) => setFarmCropCode(e.target.value)}
                  className="rounded-lg border border-line bg-card px-3 py-1.5 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-forest"
                  disabled={loadingCrops || loadingFarmAssessment}
                >
                  {crops.map((c) => (
                    <option key={c.crop_code} value={c.crop_code}>
                      {c.common_name}
                    </option>
                  ))}
                </select>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={runFarmAssessment}
                  disabled={loadingFarmAssessment}
                  className="gap-1.5"
                >
                  <RefreshCw size={13} className={loadingFarmAssessment ? "animate-spin" : ""} />
                  Refresh
                </Button>
              </div>
            </CardHeader>

            <CardContent>
              {farmError && (
                <div className="rounded-xl border border-destructive/20 bg-destructive/10 p-4 text-xs font-medium text-destructive mb-4">
                  {farmError}
                </div>
              )}

              {loadingFarmAssessment ? (
                <div className="flex h-48 items-center justify-center">
                  <Loader2 className="animate-spin text-forest" size={32} />
                </div>
              ) : farmAssessment ? (
                <div className="space-y-6">
                  {/* Top Metrics Row */}
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div className={`rounded-xl border p-4 ${getRiskColor(farmAssessment.risk_category)}`}>
                      <p className="text-xs font-semibold uppercase tracking-wider">Overall Heat Risk</p>
                      <p className="mt-1 text-2xl font-bold">{farmAssessment.risk_category}</p>
                      <p className="mt-1 text-xs opacity-90">{farmAssessment.risk_label}</p>
                    </div>

                    <div className="rounded-xl border border-line bg-card p-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted">Forecast Maximum</p>
                      <p className="mt-1 text-2xl font-bold text-forest">
                        {farmAssessment.forecast_tmax_c.toFixed(1)}°C
                      </p>
                      <p className="mt-1 text-xs text-muted">
                        Stage Threshold: {farmAssessment.critical_tmax_c.toFixed(1)}°C
                      </p>
                    </div>

                    <div className="rounded-xl border border-line bg-card p-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted">Above Critical Hours</p>
                      <p className="mt-1 text-2xl font-bold text-forest">
                        {farmAssessment.hours_above_critical.toFixed(1)} hrs
                      </p>
                      <p className="mt-1 text-xs text-muted">Estimated daytime thermal exposure</p>
                    </div>

                    <div className="rounded-xl border border-line bg-card p-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted">Warm Night Hazard</p>
                      <p className={`mt-1 text-2xl font-bold ${farmAssessment.warm_night_hazard ? "text-destructive" : "text-forest"}`}>
                        {farmAssessment.warm_night_hazard ? "Active" : "Normal"}
                      </p>
                      <p className="mt-1 text-xs text-muted">
                        Night min: {farmAssessment.forecast_tmin_c.toFixed(1)}°C
                      </p>
                    </div>
                  </div>

                  {/* 5-Day Outlook Cards */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted mb-3">
                      5-Day Forecast Thermal Trajectory
                    </h4>
                    <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 md:grid-cols-5">
                      {farmAssessment.daily_outlook?.map((day, idx) => (
                        <div key={idx} className="rounded-xl border border-line bg-card p-3 space-y-1">
                          <p className="text-xs font-bold text-foreground">{day.day_name}</p>
                          <p className="text-[11px] text-muted">{day.date}</p>
                          <div className="pt-2 flex justify-between items-baseline text-xs">
                            <span className="font-bold text-destructive">{day.tmax_c.toFixed(1)}°</span>
                            <span className="font-semibold text-muted">{day.tmin_c.toFixed(1)}°</span>
                          </div>
                          <div className="pt-1">
                            <span className={`inline-block text-[10px] font-bold px-1.5 py-0.5 rounded border ${getRiskColor(day.risk_category)}`}>
                              {day.risk_category}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Agronomic Interventions */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-forest mb-3 flex items-center gap-1.5">
                      <ShieldCheck size={16} /> Verified Crop Interventions
                    </h4>
                    <div className="space-y-3">
                      {farmAssessment.interventions?.map((inv, idx) => (
                        <div key={idx} className="rounded-xl border border-line bg-secondary/30 p-4 space-y-1">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-bold text-foreground">{inv.title}</p>
                            <Badge variant="neutral" className="text-[10px]">{inv.category}</Badge>
                          </div>
                          <p className="text-xs text-muted-foreground">{inv.description}</p>
                          <p className="text-xs text-forest pt-1">
                            <strong>Rationale:</strong> {inv.rationale}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Field Worker Safety Overview */}
                  {farmAssessment.worker_heat && (
                    <div className="rounded-xl border border-line bg-card p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">
                          <UserCheck size={15} className="text-forest" /> Field Worker Safety (WBGT)
                        </p>
                        <Badge
                          variant={farmAssessment.worker_heat.exceeds_threshold ? "destructive" : "accent"}
                        >
                          {farmAssessment.worker_heat.hazard_level} HAZARD
                        </Badge>
                      </div>
                      <p className="text-xs text-foreground font-medium">
                        {farmAssessment.worker_heat.recommendation}
                      </p>
                      <p className="text-xs text-muted">
                        Protocol: {farmAssessment.worker_heat.work_rest_cycle}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-8 text-center text-muted">
                  No farm assessment loaded yet.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── TAB 2: Manual Crop Calculator ───────────────────────────── */}
        <TabsContent value="crop" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-semibold">Crop Thermal Input</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={runCropAssessment} className="space-y-4">
                    <div>
                      <label className="text-xs font-semibold text-muted">Select Crop</label>
                      <select
                        aria-label="Select Crop"
                        value={manualCropCode}
                        onChange={(e) => {
                          setManualCropCode(e.target.value);
                          const found = crops.find((c) => c.crop_code === e.target.value);
                          if (found?.stages?.length) setManualStage(found.stages[0]);
                        }}
                        className="w-full mt-1.5 rounded-lg border border-line bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest"
                      >
                        {crops.map((c) => (
                          <option key={c.crop_code} value={c.crop_code}>
                            {c.common_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {selectedCropObj?.stages && (
                      <div>
                        <label className="text-xs font-semibold text-muted">Growth Stage</label>
                        <select
                          aria-label="Select Growth Stage"
                          value={manualStage}
                          onChange={(e) => setManualStage(e.target.value)}
                          className="w-full mt-1.5 rounded-lg border border-line bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest"
                        >
                          {selectedCropObj.stages.map((st) => (
                            <option key={st} value={st}>
                              {st.replace(/^stage_/, "").replace(/_/g, " ").toUpperCase()}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-semibold text-muted">Forecast Tmax (°C)</label>
                        <Input
                          type="number"
                          step="0.1"
                          value={manualTmax}
                          onChange={(e) => setManualTmax(e.target.value)}
                          required
                          className="mt-1.5"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-muted">Forecast Tmin (°C)</label>
                        <Input
                          type="number"
                          step="0.1"
                          value={manualTmin}
                          onChange={(e) => setManualTmin(e.target.value)}
                          required
                          className="mt-1.5"
                        />
                      </div>
                    </div>

                    <Button type="submit" disabled={loadingCropAssessment} className="w-full gap-2">
                      {loadingCropAssessment ? <Loader2 size={16} className="animate-spin" /> : <Flame size={16} />}
                      Evaluate Heat Risk
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>

            <div className="lg:col-span-7">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-semibold">Evaluation Output</CardTitle>
                </CardHeader>
                <CardContent>
                  {cropError && (
                    <div className="rounded-xl border border-destructive/20 bg-destructive/10 p-4 text-xs font-medium text-destructive mb-4">
                      {cropError}
                    </div>
                  )}

                  {cropAssessment ? (
                    <div className="space-y-4">
                      <div className={`rounded-xl border p-4 ${getRiskColor(cropAssessment.risk_category)}`}>
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-semibold uppercase tracking-wider">Thermal Risk</p>
                          <Badge variant="neutral">{cropAssessment.growth_stage_name}</Badge>
                        </div>
                        <p className="mt-1 text-2xl font-bold">{cropAssessment.risk_category}</p>
                        <p className="mt-1 text-xs opacity-90">{cropAssessment.risk_label}</p>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="rounded-xl border border-line p-3">
                          <p className="text-xs text-muted">Critical Threshold</p>
                          <p className="text-lg font-bold text-forest">{cropAssessment.critical_tmax_c}°C</p>
                        </div>
                        <div className="rounded-xl border border-line p-3">
                          <p className="text-xs text-muted">Hours Above Limit</p>
                          <p className="text-lg font-bold text-forest">{cropAssessment.hours_above_critical.toFixed(1)} hrs</p>
                        </div>
                      </div>

                      <div className="rounded-xl border border-line bg-secondary/30 p-4 space-y-2">
                        <p className="text-xs font-bold text-forest uppercase tracking-wider">Explanation</p>
                        <p className="text-xs text-foreground leading-relaxed">{cropAssessment.explanation}</p>
                        <p className="text-[11px] text-muted pt-1">
                          <strong>Citation:</strong> {cropAssessment.evidence_citation}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="py-12 text-center text-xs text-muted">
                      Enter temperatures and click &ldquo;Evaluate Heat Risk&rdquo; to calculate crop phenology impact.
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* ── TAB 3: Agricultural Worker WBGT ─────────────────────────── */}
        <TabsContent value="worker" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-semibold">Microclimate & Workload</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={runWorkerAssessment} className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-semibold text-muted">Air Temp (°C)</label>
                        <Input
                          type="number"
                          step="0.1"
                          value={workerTemp}
                          onChange={(e) => setWorkerTemp(e.target.value)}
                          required
                          className="mt-1.5"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-muted">Rel Humidity (%)</label>
                        <Input
                          type="number"
                          step="1"
                          value={workerHumidity}
                          onChange={(e) => setWorkerHumidity(e.target.value)}
                          required
                          className="mt-1.5"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-muted">Workload Category</label>
                      <select
                        aria-label="Workload Category"
                        value={workerWorkload}
                        onChange={(e) => setWorkerWorkload(e.target.value)}
                        className="w-full mt-1.5 rounded-lg border border-line bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest"
                      >
                        <option value="light">Light (Seeding, hand weeding)</option>
                        <option value="moderate">Moderate (Harvesting, spraying)</option>
                        <option value="heavy">Heavy (Tilling, manual hauling)</option>
                        <option value="very_heavy">Very Heavy (Extreme manual digging)</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-muted">Clothing Type</label>
                      <select
                        aria-label="Clothing Type"
                        value={workerClothing}
                        onChange={(e) => setWorkerClothing(e.target.value)}
                        className="w-full mt-1.5 rounded-lg border border-line bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-forest"
                      >
                        <option value="standard_work_clothes">Standard Cotton Work Clothes</option>
                        <option value="coveralls_protective">Protective Coveralls</option>
                        <option value="woven_double_layer">Double Layer / Winter Workwear</option>
                        <option value="impermeable_vapor_barrier">Impermeable Chemical Hazmat</option>
                      </select>
                    </div>

                    <Button type="submit" disabled={loadingWorkerAssessment} className="w-full gap-2">
                      {loadingWorkerAssessment ? <Loader2 size={16} className="animate-spin" /> : <HeartPulse size={16} />}
                      Calculate WBGT Index
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>

            <div className="lg:col-span-7">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-semibold">Worker Safety Assessment</CardTitle>
                </CardHeader>
                <CardContent>
                  {workerError && (
                    <div className="rounded-xl border border-destructive/20 bg-destructive/10 p-4 text-xs font-medium text-destructive mb-4">
                      {workerError}
                    </div>
                  )}

                  {workerAssessment ? (
                    <div className="space-y-4">
                      <div className={`rounded-xl border p-4 ${getRiskColor(workerAssessment.hazard_level)}`}>
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-semibold uppercase tracking-wider">Hazard Level</p>
                          <Badge variant={workerAssessment.exceeds_threshold ? "destructive" : "accent"}>
                            {workerAssessment.exceeds_threshold ? "Exceeds Threshold" : "Safe Range"}
                          </Badge>
                        </div>
                        <p className="mt-1 text-2xl font-bold">{workerAssessment.hazard_level}</p>
                        <p className="mt-1 text-xs opacity-90">{workerAssessment.recommendation}</p>
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        <div className="rounded-xl border border-line p-3">
                          <p className="text-xs text-muted">WBGT Index</p>
                          <p className="text-lg font-bold text-forest">{workerAssessment.wbgt_c.toFixed(1)}°C</p>
                        </div>
                        <div className="rounded-xl border border-line p-3">
                          <p className="text-xs text-muted">Action Limit</p>
                          <p className="text-lg font-bold text-forest">{workerAssessment.threshold_c.toFixed(1)}°C</p>
                        </div>
                        <div className="rounded-xl border border-line p-3">
                          <p className="text-xs text-muted">Heat Index</p>
                          <p className="text-lg font-bold text-forest">{workerAssessment.heat_index_c?.toFixed(1) || "—"}°C</p>
                        </div>
                      </div>

                      <div className="rounded-xl border border-line bg-secondary/30 p-4 space-y-2">
                        <p className="text-xs font-bold text-forest uppercase tracking-wider">
                          Mandatory Work-Rest Schedule
                        </p>
                        <p className="text-sm font-semibold text-foreground">
                          {workerAssessment.work_rest_cycle}
                        </p>
                        <p className="text-[11px] text-muted pt-1">
                          {workerAssessment.methodology_note}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="py-12 text-center text-xs text-muted">
                      Enter weather conditions and click &ldquo;Calculate WBGT Index&rdquo; to evaluate occupational heat safety.
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
