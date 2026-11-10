"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Calendar,
  CloudSun,
  Droplets,
  HeartPulse,
  Leaf,
  Loader2,
  MapPin,
  MapPinned,
  Pencil,
  Satellite,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { farmsApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { Farm } from "@/lib/api/types";

export default function FarmDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { selectedFarmId, farms, refreshFarms } = useFarm();

  const paramFarmId = (params?.farmId as string) || "current";
  const actualFarmId =
    paramFarmId === "current"
      ? selectedFarmId || (farms.length > 0 ? farms[0].id : null)
      : paramFarmId;

  const [farm, setFarm] = useState<Farm | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!actualFarmId) {
      setLoading(false);
      return;
    }

    let isMounted = true;
    async function loadFarm() {
      try {
        setLoading(true);
        setError(null);
        const data = await farmsApi.get(actualFarmId!);
        if (isMounted) setFarm(data);
      } catch (err: any) {
        if (isMounted) setError(err?.message || "Failed to load farm details");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadFarm();
    return () => {
      isMounted = false;
    };
  }, [actualFarmId]);

  if (loading) {
    return (
      <div className="py-24 text-center">
        <Loader2 size={32} className="mx-auto animate-spin text-leaf" />
        <p className="mt-4 text-sm text-muted">Loading farm details...</p>
      </div>
    );
  }

  if (error || !farm) {
    return (
      <div className="py-16 text-center">
        <MapPinned size={40} className="mx-auto text-muted/60" />
        <h2 className="mt-4 text-xl font-extrabold text-ink">Farm Not Found</h2>
        <p className="mt-2 text-sm text-muted">
          {error || "No farm selected or this farm does not exist in your account."}
        </p>
        <Button asChild className="mt-6">
          <Link href="/farms">Back to Farms List</Link>
        </Button>
      </div>
    );
  }

  const sections = [
    {
      title: "Soil intelligence",
      description: "Unified soil profile, chemical parameters, and lab test reports.",
      icon: Leaf,
      href: `/farms/${farm.id}/soil`,
      badge: "ISRIC & Lab",
    },
    {
      title: "Weather & climate",
      description: "Current observed conditions, 5-day forecast, and NASA POWER climate normals.",
      icon: CloudSun,
      href: `/farms/${farm.id}/weather`,
      badge: "OpenWeather",
    },
    {
      title: "Farm health",
      description: "Unified multi-domain evidence status across soil, water, weather, and satellite.",
      icon: HeartPulse,
      href: `/farms/${farm.id}/health`,
      badge: "5-Domain Gating",
    },
    {
      title: "Water intelligence",
      description: "Registered water sources, BIS water suitability, and laboratory reports.",
      icon: Droplets,
      href: `/farms/${farm.id}/water`,
      badge: "Hydrology",
    },
    {
      title: "Satellite & canopy",
      description: "Sentinel-2 L2A optical canopy vigor (NDVI/NDMI) and observation timeseries.",
      icon: Satellite,
      href: `/farms/${farm.id}/vegetation`,
      badge: "Sentinel-2",
    },
  ];

  return (
    <div className="space-y-7">
      <PageHeader
        title={farm.name}
        description={`Registered parcel in ${farm.taluka}, ${farm.district || "Pune"} district.`}
        backHref="/farms"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link href={`/farms/${farm.id}/edit`}>
                <Pencil size={15} /> Edit Farm
              </Link>
            </Button>
          </div>
        }
      />

      {/* ── Farm Overview Banner ── */}
      <Card className="border-line overflow-hidden bg-white shadow-sm">
        <CardContent className="p-6 sm:p-8">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl bg-canvas p-4 border border-line/60">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted">Calculated Area</span>
              <p className="mt-1 text-2xl font-extrabold text-ink">
                {farm.calculated_area_acres
                  ? `${farm.calculated_area_acres.toFixed(2)} acres`
                  : `${farm.calculated_area_hectares?.toFixed(2) || "—"} ha`}
              </p>
              <span className="text-[11px] text-muted block mt-0.5">
                ({farm.calculated_area_hectares?.toFixed(2) || "—"} hectares)
              </span>
            </div>

            <div className="rounded-2xl bg-canvas p-4 border border-line/60">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted">Taluka & Region</span>
              <p className="mt-1 text-2xl font-extrabold text-ink">{farm.taluka}</p>
              <span className="text-[11px] text-muted block mt-0.5">
                {farm.district || "Pune"}, Maharashtra
              </span>
            </div>

            <div className="rounded-2xl bg-canvas p-4 border border-line/60">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted">Irrigation Method</span>
              <p className="mt-1 text-2xl font-extrabold text-ink capitalize">
                {farm.irrigation_type || "Rainfed"}
              </p>
              <span className="text-[11px] text-muted block mt-0.5">
                Water source: <strong className="capitalize">{farm.water_source || "Canal"}</strong>
              </span>
            </div>

            <div className="rounded-2xl bg-canvas p-4 border border-line/60">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted">GPS Centroid</span>
              <p className="mt-1 text-lg font-extrabold text-ink font-mono">
                {farm.centroid_latitude ? farm.centroid_latitude.toFixed(4) : "—"}°N
              </p>
              <span className="text-[11px] text-muted block font-mono">
                {farm.centroid_longitude ? farm.centroid_longitude.toFixed(4) : "—"}°E
              </span>
            </div>
          </div>

          {farm.geometry && farm.geometry.coordinates?.[0] && (
            <div className="mt-6 rounded-2xl bg-[#f4f8f4] p-4 border border-[#d2e4d3] text-xs">
              <div className="flex items-center gap-2 font-bold text-forest">
                <MapPin size={16} /> Mapped Polygon Boundary
              </div>
              <p className="mt-1 text-muted text-[11px]">
                {farm.geometry.coordinates[0].length} boundary vertices recorded (GeoJSON EPSG:4326).
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Intelligence Modules ── */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-extrabold text-ink tracking-tight">Connected Intelligence</h2>
          <p className="text-xs text-muted mt-1">Specific scientific modules configured for this farm parcel.</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sections.map((sec) => {
            const Icon = sec.icon;
            return (
              <Link
                key={sec.title}
                href={sec.href}
                className="group flex flex-col justify-between rounded-card border border-line bg-white p-6 shadow-sm transition-all hover:border-leaf hover:shadow-md"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="grid size-11 place-items-center rounded-2xl bg-[#edf5ed] text-forest group-hover:bg-forest group-hover:text-white transition-colors">
                      <Icon size={20} />
                    </span>
                    <Badge variant="outline" className="text-[10px] border-line font-bold">
                      {sec.badge}
                    </Badge>
                  </div>
                  <h3 className="mt-4 text-base font-extrabold text-ink group-hover:text-forest transition-colors">
                    {sec.title}
                  </h3>
                  <p className="mt-1 text-xs leading-5 text-muted">{sec.description}</p>
                </div>
                <div className="mt-6 pt-4 border-t border-line/60 flex items-center justify-between text-xs font-bold text-forest">
                  <span>Open module</span>
                  <span className="text-lg">→</span>
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
