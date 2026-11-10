"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  CalendarDays,
  ChartNoAxesCombined,
  Clock,
  Cloud,
  CloudRain,
  CloudSun,
  Droplets,
  Loader2,
  RefreshCw,
  Sun,
  Wind,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { weatherApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { CurrentWeather, WeatherForecast, ClimateSummary } from "@/lib/api/types";

export default function WeatherPage() {
  const params = useParams();
  const { selectedFarmId, farms } = useFarm();

  const paramFarmId = (params?.farmId as string) || "current";
  const actualFarmId =
    paramFarmId === "current"
      ? selectedFarmId || (farms.length > 0 ? farms[0].id : null)
      : paramFarmId;

  const currentFarm = farms.find((f) => f.id === actualFarmId);

  const [current, setCurrent] = useState<CurrentWeather | null>(null);
  const [forecast, setForecast] = useState<WeatherForecast | null>(null);
  const [climate, setClimate] = useState<ClimateSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadWeather = async (farmId: string) => {
    try {
      setLoading(true);
      setError(null);
      const [cRes, fRes, clRes] = await Promise.allSettled([
        weatherApi.getCurrent(farmId),
        weatherApi.getForecast(farmId),
        weatherApi.getClimateSummary(farmId),
      ]);

      if (cRes.status === "fulfilled") setCurrent(cRes.value);
      if (fRes.status === "fulfilled") setForecast(fRes.value);
      if (clRes.status === "fulfilled") setClimate(clRes.value);
    } catch (err: any) {
      setError(err?.message || "Failed to load weather data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (actualFarmId) {
      loadWeather(actualFarmId);
    } else {
      setLoading(false);
    }
  }, [actualFarmId]);

  const handleRefresh = async () => {
    if (!actualFarmId) return;
    setRefreshing(true);
    await loadWeather(actualFarmId);
    setRefreshing(false);
  };

  if (!actualFarmId) {
    return (
      <div className="py-16 text-center">
        <CloudSun size={40} className="mx-auto text-muted" />
        <h2 className="mt-4 text-xl font-bold">Select a Farm</h2>
        <p className="mt-1 text-sm text-muted">Choose a farm from the header to view weather conditions.</p>
        <Button asChild className="mt-4">
          <Link href="/farms">Go to Farms</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Weather & climate"
        title={`Weather & Forecast · ${currentFarm?.name || "Farm"}`}
        description="Observed current conditions, 5-day forecast, and NASA POWER climate normals."
        backHref={`/farms/${actualFarmId}`}
        actions={
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing || loading}>
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} /> Refresh Observation
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
          <p className="mt-4 text-sm text-muted">Retrieving meteorological telemetry...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* ── Current Observation Hero ── */}
          {current ? (
            <Card className="overflow-hidden border-line bg-gradient-to-br from-white via-white to-[#f4f9f4] shadow-sm">
              <CardContent className="p-6 sm:p-8">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-[#edf5ed] text-forest border-0 font-bold">
                        Observed Conditions
                      </Badge>
                      <span className="text-[11px] text-muted">
                        Source: {current.source}
                      </span>
                    </div>
                    <div className="mt-4 flex items-baseline gap-3">
                      <span className="text-5xl font-extrabold text-ink tracking-tight">
                        {current.temperature_c.toFixed(1)}°C
                      </span>
                      <span className="text-base font-bold text-muted capitalize">
                        {current.weather_description}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-muted">
                      Feels like {current.feels_like_c != null ? `${current.feels_like_c.toFixed(1)}°C` : "—"} ·{" "}
                      Updated {new Date(current.observation_time).toLocaleTimeString()}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="rounded-2xl bg-canvas p-3 border border-line/60">
                      <span className="text-[10px] font-bold text-muted uppercase flex items-center gap-1">
                        <Droplets size={12} className="text-calm" /> Humidity
                      </span>
                      <span className="mt-1 block text-lg font-extrabold text-ink">
                        {current.humidity_percent}%
                      </span>
                    </div>

                    <div className="rounded-2xl bg-canvas p-3 border border-line/60">
                      <span className="text-[10px] font-bold text-muted uppercase flex items-center gap-1">
                        <Wind size={12} className="text-leaf" /> Wind
                      </span>
                      <span className="mt-1 block text-lg font-extrabold text-ink">
                        {current.wind_speed_ms != null ? `${current.wind_speed_ms} m/s` : "—"}
                      </span>
                    </div>

                    <div className="rounded-2xl bg-canvas p-3 border border-line/60 col-span-2 sm:col-span-1">
                      <span className="text-[10px] font-bold text-muted uppercase flex items-center gap-1">
                        <CloudRain size={12} className="text-calm" /> Rain
                      </span>
                      <span className="mt-1 block text-lg font-extrabold text-ink">
                        {current.precipitation_mm ?? 0} mm
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-8 text-center text-xs text-muted">
                Current observed weather is currently unavailable for this coordinate.
              </CardContent>
            </Card>
          )}

          {/* ── 5-Day Forecast Grid ── */}
          {forecast && forecast.forecasts && forecast.forecasts.length > 0 && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between pb-4 border-b border-line">
                  <div>
                    <h3 className="text-base font-extrabold text-ink">5-Day Forecast</h3>
                    <p className="text-xs text-muted">Upcoming atmospheric conditions for farm management</p>
                  </div>
                  <Badge variant="outline" className="text-[10px]">
                    3-Hour Intervals
                  </Badge>
                </div>

                <div className="mt-5 grid gap-3 grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 overflow-x-auto">
                  {forecast.forecasts.slice(0, 12).map((item, idx) => {
                    const date = new Date(item.timestamp);
                    return (
                      <div
                        key={idx}
                        className="rounded-2xl border border-line bg-canvas p-3 text-center flex flex-col justify-between"
                      >
                        <div>
                          <p className="text-[10px] font-bold text-muted">
                            {date.toLocaleDateString(undefined, { weekday: "short", hour: "2-digit" })}
                          </p>
                          <CloudSun size={20} className="mx-auto my-2 text-leaf" />
                          <p className="text-sm font-extrabold text-ink">
                            {item.temperature_c.toFixed(0)}°C
                          </p>
                        </div>
                        <div className="mt-2 pt-2 border-t border-line/60 text-[10px] text-muted">
                          <span>{item.precipitation_mm > 0 ? `${item.precipitation_mm}mm` : "No rain"}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── Climate Normals (NASA POWER) ── */}
          {climate && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between pb-4 border-b border-line">
                  <div>
                    <h3 className="text-base font-extrabold text-ink">NASA POWER Climate Normals</h3>
                    <p className="text-xs text-muted">
                      30-year historical baseline for agro-climatic planning in {currentFarm?.taluka}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-[10px]">
                    30-Year Climatology
                  </Badge>
                </div>

                <div className="mt-5 grid gap-4 sm:grid-cols-3">
                  <div className="rounded-2xl bg-canvas p-4 border border-line/60">
                    <span className="text-[10px] font-bold text-muted uppercase block">
                      Annual Rainfall
                    </span>
                    <p className="mt-2 text-2xl font-extrabold text-ink">
                      {climate.annual_rainfall_mm != null ? `${climate.annual_rainfall_mm} mm` : "—"}
                    </p>
                    <span className="text-[11px] text-muted mt-1 block">
                      Monsoon: {climate.monsoon_rainfall_mm ? `${climate.monsoon_rainfall_mm} mm` : "—"}
                    </span>
                  </div>

                  <div className="rounded-2xl bg-canvas p-4 border border-line/60">
                    <span className="text-[10px] font-bold text-muted uppercase block">
                      Mean Annual Temperature
                    </span>
                    <p className="mt-2 text-2xl font-extrabold text-ink">
                      {climate.mean_temperature_c != null ? `${climate.mean_temperature_c}°C` : "—"}
                    </p>
                    <span className="text-[11px] text-muted mt-1 block">
                      Pune agro-climatic zone
                    </span>
                  </div>

                  <div className="rounded-2xl bg-canvas p-4 border border-line/60">
                    <span className="text-[10px] font-bold text-muted uppercase block">
                      Seasonal Water Stress
                    </span>
                    <p className="mt-2 text-sm font-extrabold text-ink">
                      {climate.potential_water_stress_indicator || "Normal"}
                    </p>
                    <span className="text-[11px] text-muted mt-1 block">
                      Hydrological deficit profile
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
