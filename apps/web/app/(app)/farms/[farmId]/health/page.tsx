"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  ArrowRight,
  CloudSun,
  Droplets,
  HeartPulse,
  Info,
  Leaf,
  Loader2,
  RefreshCw,
  Satellite,
  ShieldAlert,
  Sprout,
  Wheat,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { farmHealthApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { FarmHealthSnapshot } from "@/lib/api/types";

function getStatusBadge(status?: string) {
  switch (status) {
    case "AVAILABLE":
      return <Badge className="bg-[#edf5ed] text-forest border-0 font-bold">Available</Badge>;
    case "PARTIALLY_AVAILABLE":
      return <Badge className="bg-orange-50 text-accent border-0 font-bold">Partial</Badge>;
    case "STALE":
      return <Badge className="bg-yellow-50 text-soil border-0 font-bold">Stale</Badge>;
    default:
      return <Badge variant="outline" className="text-muted border-line font-bold">Missing</Badge>;
  }
}

export default function FarmHealthPage() {
  const params = useParams();
  const { selectedFarmId, farms } = useFarm();

  const paramFarmId = (params?.farmId as string) || "current";
  const actualFarmId =
    paramFarmId === "current"
      ? selectedFarmId || (farms.length > 0 ? farms[0].id : null)
      : paramFarmId;

  const currentFarm = farms.find((f) => f.id === actualFarmId);

  const [snapshot, setSnapshot] = useState<FarmHealthSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [invalidating, setInvalidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSnapshot = async (farmId: string, force = false) => {
    try {
      setLoading(true);
      setError(null);
      const data = await farmHealthApi.getSnapshot(farmId, force);
      setSnapshot(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load multi-domain health snapshot");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (actualFarmId) {
      loadSnapshot(actualFarmId);
    } else {
      setLoading(false);
    }
  }, [actualFarmId]);

  const handleInvalidate = async () => {
    if (!actualFarmId) return;
    try {
      setInvalidating(true);
      await farmHealthApi.invalidate(actualFarmId);
      await loadSnapshot(actualFarmId, true);
    } catch (err: any) {
      alert(`Invalidation failed: ${err?.message || "Unknown error"}`);
    } finally {
      setInvalidating(false);
    }
  };

  if (!actualFarmId) {
    return (
      <div className="py-16 text-center">
        <HeartPulse size={40} className="mx-auto text-muted" />
        <h2 className="mt-4 text-xl font-bold">Select a Farm</h2>
        <p className="mt-1 text-sm text-muted">Choose a farm from the header to inspect its health snapshot.</p>
        <Button asChild className="mt-4">
          <Link href="/farms">Go to Farms</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Evidence-gated multi-domain health"
        title={`Farm Health Snapshot · ${currentFarm?.name || "Farm"}`}
        description="Unified evidence gating across Soil, Water, Weather, Satellite, and Crop suitability."
        backHref={`/farms/${actualFarmId}`}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={handleInvalidate}
            disabled={invalidating || loading}
          >
            <RefreshCw size={14} className={invalidating ? "animate-spin" : ""} /> Refresh Evidence Cache
          </Button>
        }
      />

      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-xs text-red-800 border border-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center">
          <Loader2 size={32} className="mx-auto animate-spin text-leaf" />
          <p className="mt-4 text-sm text-muted">Evaluating multi-domain evidence gates...</p>
        </div>
      ) : snapshot ? (
        <div className="space-y-6">
          {/* ── Summary Card ── */}
          <Card className="border-line bg-white shadow-sm overflow-hidden">
            <CardContent className="p-6 sm:p-8">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-forest text-white border-0 font-bold">
                      Domain Verification
                    </Badge>
                    <span className="text-xs text-muted font-bold">Contract v{snapshot.contract_version}</span>
                  </div>
                  <h3 className="mt-3 text-2xl font-extrabold text-ink">
                    {snapshot.overall_evidence_overview.domains_available} of {snapshot.overall_evidence_overview.total_domains} Domains Verified
                  </h3>
                  <p className="mt-1 text-xs text-muted max-w-xl">
                    {snapshot.overall_evidence_overview.actionable_summary}
                  </p>
                </div>

                <div className="flex items-center gap-2 text-center text-xs">
                  <div className="rounded-2xl bg-canvas p-3 border border-line">
                    <span className="block text-[10px] text-muted">Available</span>
                    <span className="text-lg font-extrabold text-forest">
                      {snapshot.overall_evidence_overview.domains_available}
                    </span>
                  </div>
                  <div className="rounded-2xl bg-canvas p-3 border border-line">
                    <span className="block text-[10px] text-muted">Missing</span>
                    <span className="text-lg font-extrabold text-accent">
                      {snapshot.overall_evidence_overview.domains_not_available}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-line grid grid-cols-2 sm:grid-cols-5 gap-2 text-center">
                <div className="p-3 rounded-xl bg-canvas border border-line/60">
                  <Leaf size={16} className="mx-auto text-leaf" />
                  <span className="block text-[10px] font-bold text-muted mt-1">Soil</span>
                  {getStatusBadge(snapshot.soil?.availability_state)}
                </div>
                <div className="p-3 rounded-xl bg-canvas border border-line/60">
                  <Droplets size={16} className="mx-auto text-calm" />
                  <span className="block text-[10px] font-bold text-muted mt-1">Water</span>
                  {getStatusBadge(snapshot.water?.availability_state)}
                </div>
                <div className="p-3 rounded-xl bg-canvas border border-line/60">
                  <CloudSun size={16} className="mx-auto text-accent" />
                  <span className="block text-[10px] font-bold text-muted mt-1">Weather</span>
                  {getStatusBadge(snapshot.weather?.availability_state)}
                </div>
                <div className="p-3 rounded-xl bg-canvas border border-line/60">
                  <Satellite size={16} className="mx-auto text-forest" />
                  <span className="block text-[10px] font-bold text-muted mt-1">Satellite</span>
                  {getStatusBadge(snapshot.satellite?.availability_state)}
                </div>
                <div className="p-3 rounded-xl bg-canvas border border-line/60 col-span-2 sm:col-span-1">
                  <Wheat size={16} className="mx-auto text-soil" />
                  <span className="block text-[10px] font-bold text-muted mt-1">Crop Context</span>
                  {getStatusBadge(snapshot.crop_context?.availability_state)}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ── Domains Detail Grid ── */}
          <div className="grid gap-5 md:grid-cols-2">
            {/* Soil Domain */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Leaf size={18} className="text-leaf" />
                    <h3 className="font-extrabold text-ink">Soil Domain</h3>
                  </div>
                  {getStatusBadge(snapshot.soil?.availability_state)}
                </div>

                <div className="mt-4 space-y-2 text-xs">
                  {snapshot.soil?.key_indicators && (
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 rounded-lg bg-canvas">
                        <span className="text-muted block text-[10px]">Soil pH</span>
                        <span className="font-bold text-ink">{snapshot.soil.key_indicators.soil_ph ?? "Unmeasured"}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-canvas">
                        <span className="text-muted block text-[10px]">SOC %</span>
                        <span className="font-bold text-ink">{snapshot.soil.key_indicators.organic_carbon_pct ? `${snapshot.soil.key_indicators.organic_carbon_pct}%` : "Unmeasured"}</span>
                      </div>
                    </div>
                  )}

                  {snapshot.soil?.missing_critical_parameters && snapshot.soil.missing_critical_parameters.length > 0 && (
                    <div className="rounded-lg bg-yellow-50/80 p-2.5 text-[11px] text-soil border border-yellow-200">
                      <strong>Missing parameters: </strong>
                      {snapshot.soil.missing_critical_parameters.join(", ")}
                    </div>
                  )}

                  {snapshot.soil?.agronomic_notes && (
                    <div className="space-y-1 pt-1 text-[11px] text-muted">
                      {snapshot.soil.agronomic_notes.map((note: string, idx: number) => (
                        <p key={idx}>• {note}</p>
                      ))}
                    </div>
                  )}
                </div>

                <Link
                  href={`/farms/${actualFarmId}/soil`}
                  className="mt-4 inline-flex items-center gap-1 text-xs font-bold text-forest hover:underline"
                >
                  Open Soil Intelligence →
                </Link>
              </CardContent>
            </Card>

            {/* Weather Domain */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CloudSun size={18} className="text-accent" />
                    <h3 className="font-extrabold text-ink">Weather Domain</h3>
                  </div>
                  {getStatusBadge(snapshot.weather?.availability_state)}
                </div>

                <div className="mt-4 space-y-2 text-xs">
                  {snapshot.weather?.current_weather ? (
                    <div className="p-3 rounded-xl bg-canvas border border-line">
                      <div className="flex justify-between items-baseline">
                        <span className="text-2xl font-extrabold text-ink">
                          {snapshot.weather.current_weather.temperature_c}°C
                        </span>
                        <span className="font-bold text-muted capitalize">
                          {snapshot.weather.current_weather.weather_description}
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] text-muted">
                        Humidity: {snapshot.weather.current_weather.humidity_percent}% · Wind: {snapshot.weather.current_weather.wind_speed_ms} m/s
                      </p>
                    </div>
                  ) : (
                    <p className="text-muted text-xs">No active weather observation recorded.</p>
                  )}

                  {snapshot.weather?.climate_normals && (
                    <div className="p-2.5 rounded-lg bg-canvas text-[11px] text-muted">
                      <strong>Climate normal: </strong>
                      Annual rain {snapshot.weather.climate_normals.annual_rainfall_mm}mm ({snapshot.weather.climate_normals.potential_water_stress_indicator})
                    </div>
                  )}
                </div>

                <Link
                  href={`/farms/${actualFarmId}/weather`}
                  className="mt-4 inline-flex items-center gap-1 text-xs font-bold text-forest hover:underline"
                >
                  Open Weather Planning →
                </Link>
              </CardContent>
            </Card>

            {/* Water Domain */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Droplets size={18} className="text-calm" />
                    <h3 className="font-extrabold text-ink">Water Domain</h3>
                  </div>
                  {getStatusBadge(snapshot.water?.availability_state)}
                </div>

                <div className="mt-4 space-y-2 text-xs">
                  <p className="text-muted text-xs">
                    Registered sources: <strong>{snapshot.water?.registered_sources_count ?? 0}</strong>
                  </p>
                  {snapshot.water?.missing_critical_parameters && snapshot.water.missing_critical_parameters.length > 0 && (
                    <div className="rounded-lg bg-canvas p-2.5 text-[11px] text-muted border border-line">
                      <strong>Missing parameters: </strong>
                      {snapshot.water.missing_critical_parameters.join(", ")}
                    </div>
                  )}
                </div>

                <Link
                  href={`/farms/${actualFarmId}/water`}
                  className="mt-4 inline-flex items-center gap-1 text-xs font-bold text-forest hover:underline"
                >
                  Open Water Intelligence →
                </Link>
              </CardContent>
            </Card>

            {/* Satellite Domain */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Satellite size={18} className="text-forest" />
                    <h3 className="font-extrabold text-ink">Satellite Canopy</h3>
                  </div>
                  {getStatusBadge(snapshot.satellite?.availability_state)}
                </div>

                <div className="mt-4 space-y-2 text-xs">
                  <p className="text-muted text-xs">
                    Sensor: <strong>{snapshot.satellite?.sensor || "Sentinel-2 L2A"}</strong>
                  </p>
                  <p className="text-[11px] text-muted italic">
                    {snapshot.satellite?.agronomic_interpretation || "No satellite sync executed yet for this parcel."}
                  </p>
                </div>

                <Link
                  href={`/farms/${actualFarmId}/vegetation`}
                  className="mt-4 inline-flex items-center gap-1 text-xs font-bold text-forest hover:underline"
                >
                  Open Satellite Canopy →
                </Link>
              </CardContent>
            </Card>
          </div>

          {/* Governance Notice */}
          <div className="rounded-2xl bg-canvas border border-line p-5 text-xs text-muted flex items-start gap-3">
            <Info size={17} className="text-leaf shrink-0 mt-0.5" />
            <div>
              <p className="font-extrabold text-ink">Institutional Governance Notice</p>
              <p className="mt-0.5">{snapshot.governance_notice}</p>
            </div>
          </div>
        </div>
      ) : (
        <Card>
          <CardContent className="p-12 text-center text-xs text-muted">
            Health snapshot is currently unavailable for this farm.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
