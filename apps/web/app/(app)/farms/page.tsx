"use client";

import {
  ArrowRight,
  CloudSun,
  Droplets,
  HeartPulse,
  Leaf,
  MapPin,
  MapPinned,
  Pencil,
  Plus,
  RefreshCw,
  Sprout,
} from "lucide-react";
import Link from "next/link";
import { EmptyState } from "@/components/states";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useFarm } from "@/lib/farm-context";

export default function FarmsPage() {
  const { farms, loading, refreshFarms, setSelectedFarmId, selectedFarmId } = useFarm();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Your farms"
        description="Manage mapped parcel boundaries and keep each field’s verified intelligence in one place."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refreshFarms()} disabled={loading}>
              <RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Refresh
            </Button>
            <Button asChild>
              <Link href="/farms/new">
                <Plus size={18} /> Add farm
              </Link>
            </Button>
          </div>
        }
      />

      {loading && farms.length === 0 ? (
        <div className="py-20 text-center">
          <RefreshCw size={30} className="mx-auto animate-spin text-leaf" />
          <p className="mt-4 text-sm text-muted">Retrieving registered farms...</p>
        </div>
      ) : farms.length === 0 ? (
        <Card>
          <EmptyState
            icon={MapPinned}
            title="No farms added yet"
            description="Add your first farm boundary to unlock weather forecasts, soil analysis, and crop recommendations."
            action={
              <Button asChild>
                <Link href="/farms/new">Set up a farm</Link>
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {farms.map((farm) => {
            const isSelected = farm.id === selectedFarmId;
            return (
              <Card
                key={farm.id}
                className={`overflow-hidden transition-all hover:shadow-md ${
                  isSelected ? "border-leaf ring-2 ring-leaf/20" : "border-line"
                }`}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-extrabold text-ink">{farm.name}</h3>
                        {isSelected && (
                          <Badge className="bg-[#e8f5e9] text-forest border-0 text-[10px]">
                            Active
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted mt-1 flex items-center gap-1">
                        <MapPin size={13} className="text-leaf" />
                        {farm.taluka}, {farm.district || "Pune"}
                        {farm.village ? ` · ${farm.village}` : ""}
                      </p>
                    </div>
                    <Link
                      href={`/farms/${farm.id}/edit`}
                      className="p-1.5 rounded-lg text-muted hover:text-ink hover:bg-canvas"
                      title="Edit farm"
                    >
                      <Pencil size={16} />
                    </Link>
                  </div>

                  <div className="mt-5 grid grid-cols-2 gap-2 text-xs">
                    <div className="rounded-xl bg-canvas p-2.5 border border-line/60">
                      <span className="block text-muted text-[10px] font-semibold">Area</span>
                      <span className="font-extrabold text-ink">
                        {farm.calculated_area_acres
                          ? `${farm.calculated_area_acres.toFixed(2)} ac`
                          : `${farm.calculated_area_hectares?.toFixed(2) || "—"} ha`}
                      </span>
                    </div>
                    <div className="rounded-xl bg-canvas p-2.5 border border-line/60">
                      <span className="block text-muted text-[10px] font-semibold">Irrigation</span>
                      <span className="font-extrabold text-ink capitalize">
                        {farm.irrigation_type || "Rainfed"}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-line flex items-center justify-between gap-2 text-xs">
                    <button
                      onClick={() => setSelectedFarmId(farm.id)}
                      className={`font-extrabold transition-colors ${
                        isSelected ? "text-leaf" : "text-muted hover:text-ink"
                      }`}
                    >
                      {isSelected ? "Current active parcel" : "Set as active"}
                    </button>
                    <Link
                      href={`/farms/${farm.id}`}
                      className="inline-flex items-center gap-1 font-extrabold text-forest hover:text-leaf"
                    >
                      Inspect <ArrowRight size={14} />
                    </Link>
                  </div>

                  {/* Module quick shortcuts */}
                  <div className="mt-3 grid grid-cols-4 gap-1.5 pt-2 border-t border-line/40">
                    <Link
                      href={`/farms/${farm.id}/soil`}
                      className="flex flex-col items-center p-1.5 rounded-lg hover:bg-canvas text-[10px] text-muted hover:text-ink"
                      title="Soil"
                    >
                      <Leaf size={14} className="text-leaf" />
                      <span>Soil</span>
                    </Link>
                    <Link
                      href={`/farms/${farm.id}/weather`}
                      className="flex flex-col items-center p-1.5 rounded-lg hover:bg-canvas text-[10px] text-muted hover:text-ink"
                      title="Weather"
                    >
                      <CloudSun size={14} className="text-accent" />
                      <span>Weather</span>
                    </Link>
                    <Link
                      href={`/farms/${farm.id}/health`}
                      className="flex flex-col items-center p-1.5 rounded-lg hover:bg-canvas text-[10px] text-muted hover:text-ink"
                      title="Health"
                    >
                      <HeartPulse size={14} className="text-forest" />
                      <span>Health</span>
                    </Link>
                    <Link
                      href={`/farms/${farm.id}/water`}
                      className="flex flex-col items-center p-1.5 rounded-lg hover:bg-canvas text-[10px] text-muted hover:text-ink"
                      title="Water"
                    >
                      <Droplets size={14} className="text-[#3977a8]" />
                      <span>Water</span>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
