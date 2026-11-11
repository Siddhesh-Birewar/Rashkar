"use client";

import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpenText,
  CloudSun,
  Droplets,
  Flame,
  HeartPulse,
  Leaf,
  MapPinned,
  Plus,
  RefreshCw,
  Satellite,
  ScanSearch,
  Sprout,
  Stethoscope,
  Wheat,
} from "lucide-react";
import Link from "next/link";
import { EmptyState } from "@/components/states";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionHeader } from "@/components/section-header";
import { cn } from "@/lib/utils";
import { useFarm } from "@/lib/farm-context";
import { weatherApi, farmHealthApi } from "@/lib/api/client";
import type { CurrentWeather, FarmHealthSnapshot } from "@/lib/api/types";

const quickActions = [
  {
    label: "Add farm",
    helper: "Map a new field",
    href: "/farms/new",
    icon: Plus,
    tone: "green",
  },
  {
    label: "Crop Doctor",
    helper: "Check crop symptoms",
    href: "/crop-doctor",
    icon: Stethoscope,
    tone: "orange",
  },
  {
    label: "Heat Risk",
    helper: "Crop & worker heat risk",
    href: "/heat-risk",
    icon: Flame,
    tone: "brown",
  },
] as const;

function getDomainBadge(state?: string) {
  switch (state) {
    case "AVAILABLE":
      return (
        <Badge
          variant="green"
          className="mt-1 h-5 min-h-0 w-full max-w-[68px] justify-center truncate px-1 text-[9px] font-extrabold leading-none sm:px-1.5 sm:text-[10px]"
        >
          Available
        </Badge>
      );
    case "PARTIALLY_AVAILABLE":
      return (
        <Badge
          variant="orange"
          className="mt-1 h-5 min-h-0 w-full max-w-[68px] justify-center truncate px-1 text-[9px] font-extrabold leading-none sm:px-1.5 sm:text-[10px]"
        >
          Partial
        </Badge>
      );
    case "STALE":
      return (
        <Badge
          variant="orange"
          className="mt-1 h-5 min-h-0 w-full max-w-[68px] justify-center truncate bg-yellow-50 px-1 text-[9px] font-extrabold leading-none text-soil sm:px-1.5 sm:text-[10px]"
        >
          Stale
        </Badge>
      );
    case "INSUFFICIENT_EVIDENCE":
      return (
        <Badge
          variant="neutral"
          className="mt-1 h-5 min-h-0 w-full max-w-[68px] justify-center truncate px-1 text-[8px] font-extrabold leading-none sm:px-1 sm:text-[9px]"
        >
          Low Data
        </Badge>
      );
    case "NOT_AVAILABLE":
    default:
      return (
        <Badge
          variant="neutral"
          className="mt-1 h-5 min-h-0 w-full max-w-[68px] justify-center truncate px-1 text-[9px] font-extrabold leading-none sm:px-1.5 sm:text-[10px]"
        >
          Missing
        </Badge>
      );
  }
}

export default function HomePage() {
  const { selectedFarm, selectedFarmId, farms, loading: farmsLoading } = useFarm();
  const [weather, setWeather] = useState<CurrentWeather | null>(null);
  const [health, setHealth] = useState<FarmHealthSnapshot | null>(null);
  const [loadingWeather, setLoadingWeather] = useState(false);

  const farmIdParam = selectedFarmId || (farms.length > 0 ? farms[0].id : "current");

  useEffect(() => {
    if (!selectedFarmId) {
      setWeather(null);
      setHealth(null);
      return;
    }

    let isMounted = true;
    async function loadFarmData() {
      try {
        setLoadingWeather(true);
        const [wData, hData] = await Promise.allSettled([
          weatherApi.getCurrent(selectedFarmId!),
          farmHealthApi.getSnapshot(selectedFarmId!),
        ]);

        if (!isMounted) return;

        if (wData.status === "fulfilled") {
          setWeather(wData.value);
        } else {
          setWeather(null);
        }

        if (hData.status === "fulfilled") {
          setHealth(hData.value);
        } else {
          setHealth(null);
        }
      } finally {
        if (isMounted) setLoadingWeather(false);
      }
    }

    loadFarmData();

    return () => {
      isMounted = false;
    };
  }, [selectedFarmId]);

  const intelligenceLinks = [
    {
      label: "Soil insights",
      href: `/farms/${farmIdParam}/soil`,
      icon: Leaf,
      description: "ISRIC profile & lab tests",
    },
    {
      label: "Weather planning",
      href: `/farms/${farmIdParam}/weather`,
      icon: CloudSun,
      description: "Forecasts & climate normals",
    },
    {
      label: "Farm health",
      href: `/farms/${farmIdParam}/health`,
      icon: HeartPulse,
      description: "Multi-domain evidence",
    },
    {
      label: "Water intelligence",
      href: `/farms/${farmIdParam}/water`,
      icon: Droplets,
      description: "Sources & BIS evaluation",
    },
    {
      label: "Satellite & canopy",
      href: `/farms/${farmIdParam}/vegetation`,
      icon: Satellite,
      description: "Sentinel-2 NDVI/NDMI",
    },
    {
      label: "Crop catalogue",
      href: "/crops",
      icon: Wheat,
      description: "Regional suitability specs",
    },
    {
      label: "Government schemes",
      href: "/schemes",
      icon: Sprout,
      description: "Subsidies & assistance",
    },
    {
      label: "Advisory",
      href: "/advisory",
      icon: BookOpenText,
      description: "Agronomic recommendations",
    },
  ];

  return (
    <div className="space-y-7 sm:space-y-9">
      {/* ── Top Header ── */}
      <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Badge>Farm workspace</Badge>
          <h1 className="mt-3 text-[30px] leading-[1.08] font-extrabold tracking-[-0.05em] sm:text-[38px]">
            Welcome to CropNet AI
          </h1>
          <p className="mt-2 text-sm leading-6 text-muted sm:text-[15px]">
            {selectedFarm
              ? `Active farm: ${selectedFarm.name} · ${selectedFarm.taluka}, Pune`
              : "Location-aware agricultural intelligence for Indian smallholders."}
          </p>
        </div>
        <Button asChild className="w-full sm:w-auto">
          <Link href="/farms/new">
            <Plus size={18} /> Add new farm
          </Link>
        </Button>
      </section>

      {/* ── Hero / Farm Card & Weather ── */}
      <section className="grid gap-4 lg:grid-cols-[1.4fr_.6fr]">
        <Card
          className="relative overflow-hidden border-0 bg-forest bg-cover bg-center text-white shadow-[0_20px_45px_rgba(27,94,32,.18)]"
          style={{
            backgroundImage:
              "linear-gradient(90deg, rgba(21,60,43,.98) 0%, rgba(21,60,43,.9) 52%, rgba(21,60,43,.32) 100%), url('https://images.unsplash.com/photo-1694153491575-1eb69655e4f0?auto=format&fit=crop&w=1400&q=80')",
          }}
        >
          <div className="absolute -top-14 -right-16 size-60 rounded-full border-[38px] border-white/5" />
          <div className="absolute -right-6 -bottom-16 size-40 rounded-full bg-[#4d9c52]/25 blur-sm" />
          <CardContent className="relative p-6 sm:p-8">
            <div className="flex items-start justify-between gap-4">
              <span className="grid size-11 place-items-center rounded-2xl bg-white/12">
                <MapPinned size={21} className="text-[#b7dfb9]" />
              </span>
              <Badge className="bg-white/12 text-white">
                {selectedFarm ? `${selectedFarm.taluka} Taluka` : "No farm selected"}
              </Badge>
            </div>
            <div className="mt-8 max-w-md">
              <h2 className="text-2xl font-extrabold tracking-[-0.04em] sm:text-3xl">
                {selectedFarm ? selectedFarm.name : "Start with your farm"}
              </h2>
              <p className="mt-3 text-sm leading-6 text-white/80">
                {selectedFarm ? (
                  <>
                    Area:{" "}
                    <span className="font-bold text-white">
                      {selectedFarm.calculated_area_acres
                        ? `${selectedFarm.calculated_area_acres.toFixed(2)} acres`
                        : `${selectedFarm.calculated_area_hectares?.toFixed(2) || "—"} ha`}
                    </span>
                    {" · "}
                    Irrigation:{" "}
                    <span className="capitalize font-semibold text-white">
                      {selectedFarm.irrigation_type || "Rainfed"}
                    </span>
                    {" · "}
                    Water:{" "}
                    <span className="capitalize font-semibold text-white">
                      {selectedFarm.water_source || "Canal"}
                    </span>
                  </>
                ) : (
                  "Add a farm to unlock location-aware weather, soil information, crop health and practical recommendations."
                )}
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                {selectedFarm ? (
                  <>
                    <Link
                      href={`/farms/${selectedFarm.id}`}
                      className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-white px-4 text-sm font-extrabold text-forest transition-transform active:scale-[.98]"
                    >
                      View Farm Details <ArrowRight size={17} />
                    </Link>
                    <Link
                      href={`/farms/${selectedFarm.id}/health`}
                      className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-white/15 px-4 text-sm font-bold text-white hover:bg-white/20"
                    >
                      Health Snapshot
                    </Link>
                  </>
                ) : (
                  <Link
                    href="/farms/new"
                    className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-white px-4 text-sm font-extrabold text-forest transition-transform active:scale-[.98]"
                  >
                    Set up a farm <ArrowRight size={17} />
                  </Link>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ── Weather Widget ── */}
        <Card>
          <CardContent className="flex h-full min-h-64 flex-col justify-between p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-muted">
                  Weather
                </p>
                <h2 className="mt-1 font-extrabold">Current Conditions</h2>
              </div>
              <span className="grid size-11 place-items-center rounded-2xl bg-[#edf5ed] text-leaf">
                <CloudSun size={22} />
              </span>
            </div>

            {loadingWeather ? (
              <div className="my-auto py-6 text-center">
                <RefreshCw size={24} className="mx-auto animate-spin text-leaf" />
                <p className="mt-3 text-xs text-muted">Retrieving live observation...</p>
              </div>
            ) : weather ? (
              <div className="my-auto py-4">
                <div className="flex items-baseline gap-2">
                  <p className="text-4xl font-extrabold tracking-tight text-ink">
                    {weather.temperature_c.toFixed(1)}°C
                  </p>
                  <span className="text-xs font-bold text-muted capitalize">
                    {weather.weather_description}
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg bg-canvas p-2">
                    <span className="text-muted block">Humidity</span>
                    <span className="font-bold text-ink">{weather.humidity_percent}%</span>
                  </div>
                  <div className="rounded-lg bg-canvas p-2">
                    <span className="text-muted block">Wind</span>
                    <span className="font-bold text-ink">{weather.wind_speed_ms ?? "—"} m/s</span>
                  </div>
                </div>
                <p className="mt-3 text-[10px] text-muted">Source: {weather.source} (observed)</p>
              </div>
            ) : (
              <div className="my-auto py-6 text-center">
                <p className="text-4xl font-extrabold text-[#c3cec4]">—</p>
                <p className="mt-3 text-sm font-bold">
                  {selectedFarm ? "Weather unavailable" : "Location needed"}
                </p>
                <p className="mt-1 text-xs leading-5 text-muted">
                  {selectedFarm
                    ? "Unable to fetch live observation."
                    : "Select a farm to see local conditions."}
                </p>
              </div>
            )}

            <Link
              href={selectedFarm ? `/farms/${selectedFarm.id}/weather` : "/farms"}
              className="flex min-h-11 items-center justify-center rounded-xl bg-[#f0f5f0] text-xs font-extrabold text-forest hover:bg-[#e4eee4] transition-colors"
            >
              {selectedFarm ? "View 5-day forecast" : "Choose a farm"}
            </Link>
          </CardContent>
        </Card>
      </section>

      {/* ── Quick Actions ── */}
      <section>
        <SectionHeader title="Quick actions" description="Immediate decision tools" />
        <div className="grid grid-cols-1 gap-3 min-[390px]:grid-cols-3">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.label}
                href={action.href}
                className="group rounded-card border border-line bg-white p-4 shadow-[0_8px_24px_rgba(27,65,32,.045)] transition-transform hover:-translate-y-0.5"
              >
                <span
                  className={
                    action.tone === "green"
                      ? "grid size-10 place-items-center rounded-xl bg-[#e9f4e9] text-leaf"
                      : action.tone === "orange"
                        ? "grid size-10 place-items-center rounded-xl bg-[#fff0e8] text-accent"
                        : "grid size-10 place-items-center rounded-xl bg-[#f3ece9] text-soil"
                  }
                >
                  <Icon size={19} />
                </span>
                <p className="mt-4 text-sm font-extrabold">{action.label}</p>
                <p className="mt-1 text-[11px] leading-4 text-muted">{action.helper}</p>
              </Link>
            );
          })}
        </div>
      </section>

      {/* ── Farm Intelligence Grid ── */}
      <section>
        <SectionHeader title="Crop & Field Intelligence" description="Evidence-backed modules" />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {intelligenceLinks.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                href={item.href}
                key={item.label}
                className="flex min-h-20 items-center gap-4 rounded-2xl border border-line bg-white p-4 shadow-[0_8px_24px_rgba(27,65,32,.04)] hover:border-[#b9d2ba] transition-colors"
              >
                <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-[#edf5ed] text-forest">
                  <Icon size={20} />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-extrabold">{item.label}</span>
                  <span className="mt-1 block text-[11px] text-muted">{item.description}</span>
                </span>
                <ArrowRight size={16} className="ml-auto shrink-0 text-[#9aab9c]" />
              </Link>
            );
          })}
        </div>
      </section>

      {/* ── Bottom Section: Evidence Overview & Farm Status ── */}
      <section className="grid gap-5 xl:grid-cols-2">
        <div>
          <SectionHeader title="Farm Evidence Overview" />
          <Card>
            <CardContent className="p-6">
              {health ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-extrabold text-ink">
                        {health.overall_evidence_overview.domains_available} of 5 Domains Verified
                      </p>
                      <p className="text-xs text-muted mt-1">
                        {health.overall_evidence_overview.actionable_summary}
                      </p>
                    </div>
                    <Badge variant="outline" className="border-leaf text-forest">
                      {health.overall_evidence_overview.domains_available > 0 ? "Evidence Active" : "Pending Data"}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-5 gap-1.5 sm:gap-2 text-center text-xs">
                    {[
                      { label: "Soil", state: health.soil.availability_state, icon: Leaf, iconClass: "text-leaf" },
                      { label: "Weather", state: health.weather.availability_state, icon: CloudSun, iconClass: "text-accent" },
                      { label: "Water", state: health.water.availability_state, icon: Droplets, iconClass: "text-calm" },
                      { label: "Satellite", state: health.satellite.availability_state, icon: Satellite, iconClass: "text-forest" },
                      { label: "Crops", state: health.crop_context.availability_state, icon: Wheat, iconClass: "text-soil" },
                    ].map((d) => {
                      const Icon = d.icon;
                      return (
                        <div
                          key={d.label}
                          title={`${d.label}: ${d.state || "NOT_AVAILABLE"}`}
                          className="flex min-w-0 flex-col items-center justify-between rounded-xl border border-line/70 bg-canvas p-2 sm:p-2.5 transition-colors"
                        >
                          <Icon size={14} className={cn("shrink-0", d.iconClass)} />
                          <span className="mt-1 block truncate text-[10px] font-bold text-muted sm:text-[11px]">
                            {d.label}
                          </span>
                          {getDomainBadge(d.state)}
                        </div>
                      );
                    })}
                  </div>
                  <p className="text-[11px] text-muted italic">
                    {health.governance_notice}
                  </p>
                </div>
              ) : (
                <EmptyState
                  icon={Sprout}
                  title={selectedFarm ? "No health snapshot yet" : "No farm selected"}
                  description={
                    selectedFarm
                      ? "Visit the Farm Health tab to evaluate multi-domain indicators."
                      : "Important recommendations will appear once a farm and crop profile are connected."
                  }
                />
              )}
            </CardContent>
          </Card>
        </div>
        <div>
          <SectionHeader title="Your Registered Farms" />
          <Card>
            <CardContent className="p-6">
              {farms.length > 0 ? (
                <div className="space-y-3">
                  {farms.slice(0, 3).map((f) => (
                    <div
                      key={f.id}
                      className="flex items-center justify-between p-3 rounded-xl bg-canvas border border-line"
                    >
                      <div>
                        <p className="text-sm font-extrabold text-ink">{f.name}</p>
                        <p className="text-xs text-muted">
                          {f.taluka}, Pune · {f.calculated_area_acres ? `${f.calculated_area_acres.toFixed(1)} acres` : "—"}
                        </p>
                      </div>
                      <Link
                        href={`/farms/${f.id}`}
                        className="text-xs font-bold text-leaf hover:underline"
                      >
                        Inspect
                      </Link>
                    </div>
                  ))}
                  <div className="pt-2 flex justify-between items-center text-xs">
                    <span className="text-muted">Total: {farms.length} parcels</span>
                    <Link href="/farms" className="font-extrabold text-forest hover:underline">
                      View all farms →
                    </Link>
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={BookOpenText}
                  title="No farms registered"
                  description="Add your first farm parcel to start recording field boundaries and soil assessments."
                />
              )}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
