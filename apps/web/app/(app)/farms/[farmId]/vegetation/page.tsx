"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  ExternalLink,
  Info,
  Loader2,
  RefreshCw,
  Satellite,
  ScanSearch,
  ShieldAlert,
} from "lucide-react";
import { useFarm } from "@/lib/farm-context";
import { satelliteApi, API_BASE_URL } from "@/lib/api/client";
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

  const handleSync = async () => {
    if (!actualFarmId) return;
    setSyncing(true);
    setError(null);
    setSyncMessage(null);
    try {
      const res = await satelliteApi.sync(actualFarmId);
      setSyncMessage(res?.agronomic_interpretation || "Sentinel-2 overpass synchronization completed.");
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Satellite sync failed. ESA Copernicus services may be busy.");
    } finally {
      setSyncing(false);
    }
  };

  const ndviValue = latestObs?.mean_ndvi ?? latestObs?.canopy_ndvi;
  const ndmiValue = latestObs?.mean_ndmi ?? latestObs?.canopy_ndmi;

  return (
    <div className="space-y-6 sm:space-y-8">
      <PageHeader
        eyebrow="Satellite & vegetation"
        title="Field observations from space"
        description="Sentinel-2 multispectral surface reflectance (10m resolution) for canopy vigor and moisture dynamics."
        actions={
          <Button onClick={handleSync} disabled={syncing} className="gap-2">
            {syncing ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
            {syncing ? "Synchronizing Sentinel-2..." : "Sync Sentinel-2"}
          </Button>
        }
      />

      {syncMessage && (
        <div className="flex items-center gap-2 rounded-xl border border-primary/20 bg-primary/10 p-4 text-sm font-medium text-forest">
          <Satellite size={18} className="shrink-0 text-primary" />
          <span>{syncMessage}</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 p-4 text-sm font-medium text-destructive">
          <ShieldAlert size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Scientific Disclaimer */}
      <div className="flex gap-3 rounded-2xl border border-[#cde0ce] bg-[#f1f8f1] p-4 text-sm text-forest">
        <Info className="mt-0.5 shrink-0" size={19} />
        <div className="text-xs leading-5 sm:text-sm">
          <strong>Scientific Integrity Guardrail:</strong> Sentinel-2 optical reflectance captures canopy biomass and chlorophyll vigor (NDVI) and moisture absorption (NDMI). Under no circumstances are satellite indices treated as direct pathogen diagnosis, nitrogen measurements, or final yield projections.
        </div>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="animate-spin text-forest" size={32} />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Latest Observation Hero */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted">Canopy NDVI (Greenness)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-forest">
                  {ndviValue !== null && ndviValue !== undefined ? ndviValue.toFixed(2) : "—"}
                </div>
                <p className="mt-1 text-xs text-muted">
                  {ndviValue !== null && ndviValue !== undefined
                    ? ndviValue >= 0.6
                      ? "Dense vegetative canopy"
                      : ndviValue >= 0.4
                      ? "Moderate greenness"
                      : ndviValue >= 0.2
                      ? "Sparse canopy / young crop"
                      : "Bare soil or crop residue"
                    : "No verified observation"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted">Canopy NDMI (Moisture)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-forest">
                  {ndmiValue !== null && ndmiValue !== undefined ? ndmiValue.toFixed(2) : "—"}
                </div>
                <p className="mt-1 text-xs text-muted">
                  {ndmiValue !== null && ndmiValue !== undefined
                    ? ndmiValue >= 0.3
                      ? "High canopy water content"
                      : ndmiValue >= 0.0
                      ? "Adequate moisture vigor"
                      : "Low moisture / water stress"
                    : "No verified observation"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted">Observation Date</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold text-forest">
                  {latestObs?.observation_date
                    ? new Date(latestObs.observation_date).toLocaleDateString("en-IN", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })
                    : "None recorded"}
                </div>
                <p className="mt-1 text-xs text-muted">
                  {latestObs?.sensor || "Copernicus Sentinel-2 Level-2A"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted">Quality & Pixels</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold text-forest">
                  {latestObs?.valid_pixel_count ? `${latestObs.valid_pixel_count} pixels` : "0 valid"}
                </div>
                <p className="mt-1 text-xs text-muted">
                  Cloud masked: {latestObs?.cloud_masked_percent != null ? `${latestObs.cloud_masked_percent}%` : "0%"}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Raster Visual Maps */}
          {actualFarmId && latestObs && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <ScanSearch size={18} className="text-forest" />
                  Calibrated Raster Previews
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-xl border border-line bg-card p-4">
                    <p className="text-sm font-semibold">NDVI Reflectance Layer</p>
                    <p className="mt-1 text-xs text-muted">Color-mapped vegetation index raster for parcel boundary.</p>
                    <Button variant="outline" size="sm" asChild className="mt-3 gap-2">
                      <a
                        href={`${API_BASE_URL}/api/v1/farms/${actualFarmId}/satellite/latest/raster-map?layer=ndvi`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open Raster View <ExternalLink size={14} />
                      </a>
                    </Button>
                  </div>

                  <div className="rounded-xl border border-line bg-card p-4">
                    <p className="text-sm font-semibold">NDMI Moisture Layer</p>
                    <p className="mt-1 text-xs text-muted">Shortwave infrared water absorption index map.</p>
                    <Button variant="outline" size="sm" asChild className="mt-3 gap-2">
                      <a
                        href={`${API_BASE_URL}/api/v1/farms/${actualFarmId}/satellite/latest/raster-map?layer=ndmi`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open Raster View <ExternalLink size={14} />
                      </a>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Time Series History */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold">Observation History & Trends</CardTitle>
                <p className="text-xs text-muted">Authentic Copernicus observations recorded for this parcel boundary.</p>
              </div>
              <Badge variant="neutral">
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
                        <th className="pb-2 font-medium">Valid Pixels</th>
                        <th className="pb-2 font-medium">Cloud %</th>
                        <th className="pb-2 font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/60">
                      {timeseriesData.series.map((item: any, idx: number) => (
                        <tr key={idx} className="hover:bg-muted/10">
                          <td className="py-2 font-medium text-foreground">
                            {new Date(item.date).toLocaleDateString("en-IN", {
                              day: "numeric",
                              month: "short",
                              year: "numeric",
                            })}
                          </td>
                          <td className="py-2 text-forest font-semibold">{item.mean_ndvi?.toFixed(2) ?? "—"}</td>
                          <td className="py-2 text-forest font-semibold">{item.mean_ndmi?.toFixed(2) ?? "—"}</td>
                          <td className="py-2">{item.valid_pixels}</td>
                          <td className="py-2">{item.cloud_masked_percent != null ? `${item.cloud_masked_percent}%` : "—"}</td>
                          <td className="py-2">
                            <Badge variant={item.quality_status === "VALID" ? "accent" : "neutral"}>
                              {item.quality_status || "OK"}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-8 text-center">
                  <Satellite className="mx-auto text-muted/60" size={36} />
                  <p className="mt-2 text-sm font-semibold">No satellite observations recorded yet</p>
                  <p className="mt-1 text-xs text-muted max-w-sm mx-auto">
                    Click &ldquo;Sync Sentinel-2&rdquo; to query the ESA Copernicus planetary archive for latest cloud-free acquisitions over {farm?.name || "this parcel"}.
                  </p>
                  <Button onClick={handleSync} disabled={syncing} size="sm" className="mt-4 gap-2">
                    <RefreshCw size={14} /> Sync Sentinel-2 Now
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
