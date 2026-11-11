"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  Download,
  ExternalLink,
  Info,
  Layers,
  Loader2,
  RefreshCw,
  Satellite,
  ScanSearch,
  ShieldAlert,
  X,
  CheckCircle2,
} from "lucide-react";
import { useFarm } from "@/lib/farm-context";
import { satelliteApi, API_BASE_URL, getAuthHeaders } from "@/lib/api/client";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function VegetationPage() {
  const params = useParams();
  const farmIdParam = params?.farmId as string;
  const { selectedFarm, farms, selectedFarmId } = useFarm();

  const actualFarmId =
    farmIdParam && farmIdParam !== "current"
      ? farmIdParam
      : selectedFarmId || farms[0]?.id;

  const farm = farms.find((f) => f.id === actualFarmId) || selectedFarm;

  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [latestObs, setLatestObs] = useState<any | null>(null);
  const [timeseriesData, setTimeseriesData] = useState<any | null>(null);

  // Raster viewer modal state
  const [activeRaster, setActiveRaster] = useState<"ndvi" | "ndmi" | null>(null);
  const [rasterUrl, setRasterUrl] = useState<string | null>(null);
  const [rasterLoading, setRasterLoading] = useState(false);
  const [rasterError, setRasterError] = useState<string | null>(null);

  const loadData = async () => {
    if (!actualFarmId) return;
    setLoading(true);
    setError(null);
    try {
      const [latestRes, tsRes] = await Promise.allSettled([
        satelliteApi.getLatest(actualFarmId),
        satelliteApi.getTimeseries(actualFarmId),
      ]);

      if (latestRes.status === "fulfilled") {
        setLatestObs(latestRes.value);
      } else {
        setLatestObs(null);
      }

      if (tsRes.status === "fulfilled") {
        setTimeseriesData(tsRes.value);
      } else {
        setTimeseriesData(null);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load satellite observation data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [actualFarmId]);

  const handleSyncSentinel = async () => {
    if (!actualFarmId) return;
    setSyncing(true);
    setError(null);
    setSyncMessage(null);
    try {
      const result = await satelliteApi.sync(actualFarmId);
      setSyncMessage(
        result?.agronomic_interpretation || "Sentinel-2 overpass synchronization completed."
      );
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Satellite sync failed. ESA Copernicus services may be busy.");
    } finally {
      setSyncing(false);
    }
  };

  const handleOpenRaster = async (indexType: "ndvi" | "ndmi") => {
    if (!actualFarmId) return;
    setActiveRaster(indexType);
    setRasterLoading(true);
    setRasterError(null);
    setRasterUrl(null);

    try {
      const authHeaders = getAuthHeaders();
      const url = `${API_BASE_URL.replace(/\/$/, "")}/api/v1/farms/${actualFarmId}/satellite/latest/raster-map?index_type=${indexType}`;
      const res = await fetch(url, { headers: authHeaders });

      if (!res.ok) {
        throw new Error(`Raster extraction returned HTTP ${res.status}.`);
      }

      const blob = await res.blob();
      const objUrl = URL.createObjectURL(blob);
      setRasterUrl(objUrl);
    } catch (err: any) {
      setRasterError(
        err?.message || "Could not retrieve raster map. Please ensure satellite overpass is synced."
      );
    } finally {
      setRasterLoading(false);
    }
  };

  const handleCloseRaster = () => {
    if (rasterUrl) {
      URL.revokeObjectURL(rasterUrl);
    }
    setActiveRaster(null);
    setRasterUrl(null);
    setRasterError(null);
  };

  const meanNdvi = latestObs?.mean_ndvi ?? latestObs?.canopy_ndvi;
  const meanNdmi = latestObs?.mean_ndmi ?? latestObs?.canopy_ndmi;

  return (
    <div className="space-y-6 sm:space-y-8">
      <PageHeader
        eyebrow="Satellite & vegetation"
        title="Field observations from space"
        description="Sentinel-2 multispectral surface reflectance (10m resolution) for canopy vigor and moisture dynamics."
        backHref={`/farms/${actualFarmId}`}
        actions={
          <Button onClick={handleSyncSentinel} disabled={syncing} className="gap-2 bg-forest">
            {syncing ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
            {syncing ? "Synchronizing Sentinel-2..." : "Sync Sentinel-2"}
          </Button>
        }
      />

      {syncMessage && (
        <div className="flex items-center gap-2 rounded-xl border border-primary/20 bg-primary/10 p-4 text-sm font-medium text-forest">
          <CheckCircle2 size={18} className="shrink-0 text-leaf" />
          <span>{syncMessage}</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 p-4 text-sm font-medium text-destructive">
          <ShieldAlert size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="flex gap-3 rounded-2xl border border-[#cde0ce] bg-[#f1f8f1] p-4 text-sm text-forest">
        <Info size={19} className="mt-0.5 shrink-0" />
        <div className="text-xs leading-5 sm:text-sm">
          <strong>Scientific Integrity Guardrail:</strong> Sentinel-2 optical reflectance captures
          canopy biomass and chlorophyll vigor (NDVI) and moisture absorption (NDMI). Under no
          circumstances are satellite indices treated as direct pathogen diagnosis, nitrogen
          measurements, or final yield projections.
        </div>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="animate-spin text-forest" size={32} />
        </div>
      ) : (
        <div className="space-y-6">
          {/* ── Top Metrics ── */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Canopy NDVI (Greenness)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-forest">
                  {meanNdvi != null ? meanNdvi.toFixed(2) : "—"}
                </div>
                <p className="mt-1 text-xs text-muted">
                  {meanNdvi != null
                    ? meanNdvi >= 0.6
                      ? "Dense vegetative canopy"
                      : meanNdvi >= 0.4
                        ? "Moderate greenness"
                        : meanNdvi >= 0.2
                          ? "Sparse canopy / young crop"
                          : "Bare soil or crop residue"
                    : "No verified observation"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Canopy NDMI (Moisture)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-forest">
                  {meanNdmi != null ? meanNdmi.toFixed(2) : "—"}
                </div>
                <p className="mt-1 text-xs text-muted">
                  {meanNdmi != null
                    ? meanNdmi >= 0.3
                      ? "High canopy water content"
                      : meanNdmi >= 0.0
                        ? "Adequate moisture vigor"
                        : "Low moisture / water stress"
                    : "No verified observation"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Scene Cloud Cover
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-forest">
                  {latestObs?.cloud_coverage_percentage != null
                    ? `${latestObs.cloud_coverage_percentage.toFixed(1)}%`
                    : "—"}
                </div>
                <p className="mt-1 text-xs text-muted">
                  {latestObs?.cloud_coverage_percentage != null
                    ? latestObs.cloud_coverage_percentage < 15
                      ? "Optimal optical clarity (<15%)"
                      : "Partial cloud interference"
                    : "Overpass pending"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Last Observation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-base font-bold text-forest">
                  {latestObs?.observation_date
                    ? new Date(latestObs.observation_date).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })
                    : "—"}
                </div>
                <p className="mt-1 text-xs text-muted">
                  Copernicus Sentinel-2 L2A (10m)
                </p>
              </CardContent>
            </Card>
          </div>

          {/* ── Calibrated Raster Previews ── */}
          {actualFarmId && (
            <Card className="border-line shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <ScanSearch size={18} className="text-forest" />
                  Calibrated 2D Raster Previews
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  {/* NDVI Layer Card */}
                  <div className="rounded-2xl border border-line bg-canvas p-5 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-extrabold text-ink">NDVI Reflectance Layer</span>
                        <Badge className="bg-[#edf5ed] text-forest border-0 text-[10px] font-bold">
                          10m Optical
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted leading-relaxed">
                        Color-mapped vegetation index raster clipped precisely to your farm boundary polygon.
                      </p>

                      <div className="mt-3 flex items-center gap-2 text-[11px] text-muted">
                        <span className="inline-block size-2 rounded-full bg-leaf" />
                        <span>Greenness: {meanNdvi != null ? meanNdvi.toFixed(2) : "Calculated on sync"}</span>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-line/60 flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenRaster("ndvi")}
                        className="gap-2 text-xs bg-white hover:bg-forest hover:text-white transition-colors"
                      >
                        <ScanSearch size={14} /> Open Raster View
                      </Button>
                    </div>
                  </div>

                  {/* NDMI Layer Card */}
                  <div className="rounded-2xl border border-line bg-canvas p-5 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-extrabold text-ink">NDMI Moisture Layer</span>
                        <Badge className="bg-[#edf5ed] text-forest border-0 text-[10px] font-bold">
                          20m SWIR
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted leading-relaxed">
                        Shortwave infrared water absorption index map revealing internal crop leaf hydration.
                      </p>

                      <div className="mt-3 flex items-center gap-2 text-[11px] text-muted">
                        <span className="inline-block size-2 rounded-full bg-calm" />
                        <span>Moisture: {meanNdmi != null ? meanNdmi.toFixed(2) : "Calculated on sync"}</span>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-line/60 flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenRaster("ndmi")}
                        className="gap-2 text-xs bg-white hover:bg-forest hover:text-white transition-colors"
                      >
                        <ScanSearch size={14} /> Open Raster View
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── Time Series History ── */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold">Observation History & Trends</CardTitle>
                <p className="text-xs text-muted">Authentic Copernicus observations recorded for this parcel boundary.</p>
              </div>
              <Badge variant="outline">
                {timeseriesData?.total_observations || 0} observations
              </Badge>
            </CardHeader>
            <CardContent>
              {timeseriesData?.vegetation_interpretation && (
                <div className="mb-4 rounded-xl border border-primary/20 bg-secondary/30 p-3 text-xs leading-relaxed text-forest">
                  <strong>Agronomic Interpretation:</strong> {timeseriesData.vegetation_interpretation}
                </div>
              )}

              {timeseriesData?.series && timeseriesData.series.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-line text-muted">
                        <th className="pb-2 font-medium">Date</th>
                        <th className="pb-2 font-medium">Mean NDVI</th>
                        <th className="pb-2 font-medium">Mean NDMI</th>
                        <th className="pb-2 font-medium">Cloud Cover</th>
                        <th className="pb-2 font-medium">Clear Pixels</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/60">
                      {timeseriesData.series.map((row: any, i: number) => (
                        <tr key={i} className="hover:bg-muted/5">
                          <td className="py-2.5 font-medium">
                            {new Date(row.observation_date).toLocaleDateString()}
                          </td>
                          <td className="py-2.5 font-bold text-forest">
                            {row.mean_ndvi != null ? row.mean_ndvi.toFixed(2) : "—"}
                          </td>
                          <td className="py-2.5 font-bold text-forest">
                            {row.mean_ndmi != null ? row.mean_ndmi.toFixed(2) : "—"}
                          </td>
                          <td className="py-2.5 text-muted">
                            {row.cloud_coverage_percentage != null
                              ? `${row.cloud_coverage_percentage.toFixed(1)}%`
                              : "—"}
                          </td>
                          <td className="py-2.5 text-muted">{row.valid_pixel_count ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-muted">
                  No multi-temporal timeseries recorded yet. Tap &quot;Sync Sentinel-2&quot; above to capture current satellite telemetry.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── Interactive Calibrated Raster Modal ── */}
      {activeRaster && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-line">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div className="flex items-center gap-2">
                <span className="grid size-8 place-items-center rounded-xl bg-forest/10 text-forest">
                  <Satellite size={17} />
                </span>
                <div>
                  <h3 className="text-sm font-extrabold text-ink uppercase tracking-wide">
                    {activeRaster === "ndvi"
                      ? "Sentinel-2 NDVI Canopy Vigor Layer"
                      : "Sentinel-2 NDMI Leaf Moisture Layer"}
                  </h3>
                  <p className="text-[11px] text-muted">
                    {activeRaster === "ndvi" ? "B04/B08 10m Optical Raster" : "B08/B11 20m Resampled SWIR"}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleCloseRaster}
                className="grid size-8 place-items-center rounded-lg text-muted hover:bg-canvas hover:text-ink transition"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-4 flex flex-col items-center justify-center min-h-64 rounded-xl bg-[#131b15] p-4 text-center">
              {rasterLoading ? (
                <div className="py-12 text-center text-white/80">
                  <Loader2 size={32} className="animate-spin mx-auto text-leaf" />
                  <p className="mt-3 text-xs">Extracting calibrated satellite raster...</p>
                </div>
              ) : rasterError ? (
                <div className="py-8 px-4 text-xs text-red-300">
                  <p className="font-bold text-red-200">Raster Extraction Notice</p>
                  <p className="mt-1">{rasterError}</p>
                  <p className="mt-3 text-[11px] text-white/60">
                    Satellite raster is generated upon Sentinel-2 overpass synchronization.
                  </p>
                  <Button
                    size="sm"
                    onClick={async () => {
                      if (!activeRaster) return;
                      const currentType = activeRaster;
                      await handleSyncSentinel();
                      await handleOpenRaster(currentType);
                    }}
                    disabled={syncing}
                    className="mt-4 bg-forest text-xs gap-1.5 text-white"
                  >
                    <RefreshCw size={13} className={syncing ? "animate-spin" : ""} />
                    {syncing ? "Synchronizing Sentinel-2..." : "Sync Sentinel-2 & Load Raster"}
                  </Button>
                </div>
              ) : rasterUrl ? (
                <div className="space-y-3">
                  <div className="overflow-hidden rounded-lg border border-white/20 bg-black shadow-inner">
                    <img
                      src={rasterUrl}
                      alt={`${activeRaster.toUpperCase()} raster preview`}
                      className="max-h-72 w-auto mx-auto object-contain [image-rendering:pixelated]"
                    />
                  </div>
                  <p className="text-[10px] text-white/70">
                    Clipped to farm boundary with authenticated coordinate spatial projection
                  </p>
                </div>
              ) : null}
            </div>

            {/* Colormap Legend Bar */}
            <div className="mt-4 space-y-2 rounded-xl bg-canvas p-3 border border-line text-xs">
              <span className="font-bold text-ink block text-[11px]">
                {activeRaster === "ndvi" ? "NDVI Colormap Scale:" : "NDMI Colormap Scale:"}
              </span>
              {activeRaster === "ndvi" ? (
                <div className="space-y-1">
                  <div className="h-3 w-full rounded-full bg-gradient-to-r from-[#d73027] via-[#fee08b] via-[#a6d96a] to-[#1a9850]" />
                  <div className="flex justify-between text-[10px] text-muted">
                    <span>&lt; 0.2 (Bare soil)</span>
                    <span>0.4 (Moderate)</span>
                    <span>&gt; 0.7 (Dense Canopy)</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-1">
                  <div className="h-3 w-full rounded-full bg-gradient-to-r from-[#8c510a] via-[#f6e8c3] via-[#80cdc1] to-[#01665e]" />
                  <div className="flex justify-between text-[10px] text-muted">
                    <span>&lt; 0.0 (Water Stress)</span>
                    <span>0.2 (Adequate)</span>
                    <span>&gt; 0.4 (High Hydration)</span>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-5 flex justify-end gap-2">
              {rasterUrl && (
                <Button variant="secondary" size="sm" asChild className="text-xs gap-1.5">
                  <a href={rasterUrl} download={`${activeRaster}_farm_raster.png`}>
                    <Download size={14} /> Download PNG
                  </a>
                </Button>
              )}
              <Button onClick={handleCloseRaster} size="sm" className="bg-forest text-xs">
                Close Viewer
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
