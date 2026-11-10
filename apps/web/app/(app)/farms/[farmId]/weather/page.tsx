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
  Info,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { weatherApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { CurrentWeather, WeatherForecast, ClimateSummary, DailyForecastSummary } from "@/lib/api/types";

function getWeatherIcon(condition?: string) {
  const cond = condition?.toLowerCase() || "";
  if (cond.includes("rain") || cond.includes("drizzle") || cond.includes("thunder")) {
    return <CloudRain size={22} className="text-calm mx-auto my-2" />;
  }
  if (cond.includes("cloud") || cond.includes("overcast")) {
    return <CloudSun size={22} className="text-leaf mx-auto my-2" />;
  }
  return <Sun size={22} className="text-amber-500 mx-auto my-2" />;
}

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

  // Get daily summaries from backend
  const dailySummaries = forecast?.daily_summaries || [];
  const hourlyPoints = forecast?.hourly_points || forecast?.forecasts || [];

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

          {/* ── 5-Day Forecast Grid (Daily Summaries) ── */}
          {dailySummaries.length > 0 && (
            <Card className="border-line shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between pb-4 border-b border-line">
                  <div>
                    <h3 className="text-base font-extrabold text-ink">5-Day Agricultural Weather Forecast</h3>
                    <p className="text-xs text-muted">Daily agro-meteorological projections for field operations & spray planning</p>
                  </div>
                  <Badge className="bg-[#edf5ed] text-forest border-0 text-[10px] font-bold">
                    OpenWeather 5-Day
                  </Badge>
                </div>

                <div className="mt-5 grid gap-3 grid-cols-2 sm:grid-cols-5">
                  {dailySummaries.map((day, idx) => {
                    const isToday = idx === 0;
                    return (
                      <div
                        key={day.date}
                        className={`rounded-2xl border p-4 text-center flex flex-col justify-between transition-all ${
                          isToday
                            ? "border-leaf/50 bg-[#f4f9f4] shadow-sm"
                            : "border-line bg-canvas hover:border-leaf/30"
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-center gap-1">
                            <span className="text-xs font-bold text-ink">
                              {isToday ? "Today" : day.day_name}
                            </span>
                            {isToday && (
                              <span className="inline-block size-1.5 rounded-full bg-leaf" />
                            )}
                          </div>
                          <p className="text-[10px] text-muted mt-0.5">{day.date}</p>

                          {getWeatherIcon(day.weather_condition)}

                          <p className="text-xs font-semibold text-ink capitalize truncate">
                            {day.weather_description}
                          </p>

                          <div className="mt-2 flex items-baseline justify-center gap-1.5">
                            <span className="text-lg font-extrabold text-ink">
                              {day.temp_max_c.toFixed(0)}°
                            </span>
                            <span className="text-xs font-medium text-muted">
                              / {day.temp_min_c.toFixed(0)}°C
                            </span>
                          </div>
                        </div>

                        <div className="mt-3 pt-2.5 border-t border-line/60 grid grid-cols-2 gap-1 text-[10px] text-muted">
                          <div>
                            <span className="block text-[9px] uppercase tracking-wider text-muted/70">Rain</span>
                            <strong className="text-ink">{day.total_rain_mm > 0 ? `${day.total_rain_mm}mm` : "0 mm"}</strong>
                          </div>
                          <div>
                            <span className="block text-[9px] uppercase tracking-wider text-muted/70">Humidity</span>
                            <strong className="text-ink">{day.humidity_percent.toFixed(0)}%</strong>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── 3-Hour Interval Timeline ── */}
          {hourlyPoints.length > 0 && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between pb-4 border-b border-line">
                  <div>
                    <h3 className="text-base font-extrabold text-ink">3-Hour Interval Progression</h3>
                    <p className="text-xs text-muted">Detailed temperature, wind, and rain probability timeline</p>
                  </div>
                  <Badge variant="outline" className="text-[10px]">
                    Telemetry Resolution: 3h
                  </Badge>
                </div>

                <div className="mt-5 flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
                  {hourlyPoints.slice(0, 12).map((item, idx) => {
                    const timeStr = item.forecast_time || item.timestamp || "";
                    const date = timeStr ? new Date(timeStr) : new Date();
                    return (
                      <div
                        key={idx}
                        className="min-w-[105px] shrink-0 rounded-2xl border border-line bg-canvas p-3 text-center flex flex-col justify-between"
                      >
                        <div>
                          <p className="text-[10px] font-bold text-muted">
                            {date.toLocaleDateString(undefined, { weekday: "short" })}{" "}
                            {date.toLocaleTimeString(undefined, { hour: "numeric" })}
                          </p>
                          {getWeatherIcon(item.weather_condition)}
                          <p className="text-sm font-extrabold text-ink">
                            {item.temperature_c.toFixed(0)}°C
                          </p>
                        </div>
                        <div className="mt-2 pt-2 border-t border-line/60 text-[10px] text-muted">
                          <span>
                            {item.precipitation_mm > 0 ? `${item.precipitation_mm}mm` : "No rain"}
                          </span>
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
                  <div className="rounded-2xl border border-line bg-canvas p-4">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted block">
                      Annual Rainfall
                    </span>
                    <p className="mt-2 text-2xl font-extrabold text-ink">
                      {climate.annual_rainfall_mm != null ? `${climate.annual_rainfall_mm} mm` : "—"}
                    </p>
                    <span className="mt-1 block text-xs text-muted">
                      Monsoon: {climate.monsoon_rainfall_mm != null ? `${climate.monsoon_rainfall_mm} mm` : "—"}
                    </span>
                  </div>

                  <div className="rounded-2xl border border-line bg-canvas p-4">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted block">
                      Mean Annual Temperature
                    </span>
                    <p className="mt-2 text-2xl font-extrabold text-ink">
                      {climate.mean_temperature_c != null ? `${climate.mean_temperature_c.toFixed(1)}°C` : "—"}
                    </p>
                    <span className="mt-1 block text-xs text-muted">
                      Agro-climatic zone: Plain Zone Vertisols
                    </span>
                  </div>

                  <div className="rounded-2xl border border-line bg-canvas p-4">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted block">
                      Water Stress Assessment
                    </span>
                    <p className="mt-2 text-base font-extrabold text-forest capitalize">
                      {climate.potential_water_stress_indicator || "Low Risk"}
                    </p>
                    <span className="mt-1 block text-xs text-muted">
                      Protective summer irrigation advised
                    </span>
                  </div>
                </div>

                {climate.notes && climate.notes.length > 0 && (
                  <div className="mt-5 rounded-xl border border-line bg-[#fdfdfc] p-4 text-xs text-muted">
                    <strong className="text-ink">Agro-Climatic Insights:</strong>
                    <ul className="mt-1 list-disc pl-4 space-y-0.5">
                      {climate.notes.map((note, i) => (
                        <li key={i}>{note}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
