"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  BarChart3,
  CircleDollarSign,
  Flame,
  LayoutDashboard,
  MapPin,
  Plus,
  Sprout,
  ThermometerSun,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { EmptyState, LoadingState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useFarm } from "@/lib/farm-context";
import type { Farm } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { rashkarApi } from "../lib/api";
import { formatCropLabel, formatTokenLabel } from "../lib/format";
import type { RashkarOverviewResponse } from "../types";
import { CropCycleDialog } from "./CropCycleDialog";

export type RashkarTabKey =
  | "overview"
  | "worker-heat"
  | "crop-heat"
  | "yield"
  | "earn-more";

const RASHKAR_TABS: Array<{
  key: RashkarTabKey;
  label: string;
  href: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}> = [
  { key: "overview", label: "Overview", href: "/rashkar", icon: LayoutDashboard },
  { key: "worker-heat", label: "Worker Heat", href: "/rashkar/worker-heat", icon: ThermometerSun },
  { key: "crop-heat", label: "Crop Heat", href: "/rashkar/crop-heat", icon: Flame },
  { key: "yield", label: "Yield Intelligence", href: "/rashkar/yield", icon: BarChart3 },
  { key: "earn-more", label: "Earn More", href: "/rashkar/earn-more", icon: CircleDollarSign },
];

interface RashkarShellContextValue {
  farm: Farm | null;
  overview: RashkarOverviewResponse | null;
  overviewLoading: boolean;
  overviewError: string | null;
  cycleVersion: number;
  openCropDialog: () => void;
  refreshOverview: () => Promise<void>;
  notifyCycleChanged: () => void;
}

const RashkarShellContext = createContext<RashkarShellContextValue>({
  farm: null,
  overview: null,
  overviewLoading: false,
  overviewError: null,
  cycleVersion: 0,
  openCropDialog: () => {},
  refreshOverview: async () => {},
  notifyCycleChanged: () => {},
});

export function useRashkarShell() {
  return useContext(RashkarShellContext);
}

interface RashkarShellProps {
  activeTab: RashkarTabKey;
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}

export function RashkarShell({
  activeTab,
  eyebrow = "RASHKAR Field Intelligence",
  title,
  description,
  actions,
  children,
}: RashkarShellProps) {
  const { farms, selectedFarm, loading: farmsLoading } = useFarm();
  const [overview, setOverview] = useState<RashkarOverviewResponse | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewError, setOverviewError] = useState<string | null>(null);
  const [cycleVersion, setCycleVersion] = useState(0);
  const [cropDialogOpen, setCropDialogOpen] = useState(false);

  const loadOverview = useCallback(async (farmId: string) => {
    setOverviewLoading(true);
    setOverviewError(null);
    try {
      const data = await rashkarApi.getOverview(farmId);
      setOverview(data);
    } catch (err: any) {
      setOverviewError(err?.message || "Failed to load farm RASHKAR context.");
      setOverview(null);
    } finally {
      setOverviewLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!selectedFarm?.id) {
      setOverview(null);
      setOverviewError(null);
      return;
    }
    loadOverview(selectedFarm.id);
  }, [selectedFarm?.id, cycleVersion, loadOverview]);

  const notifyCycleChanged = useCallback(() => {
    setCycleVersion((v) => v + 1);
  }, []);

  const refreshOverview = useCallback(async () => {
    if (selectedFarm?.id) {
      await loadOverview(selectedFarm.id);
    }
  }, [selectedFarm?.id, loadOverview]);

  const activeCycle = overview?.active_crop_cycle ?? null;

  return (
    <RashkarShellContext.Provider
      value={{
        farm: selectedFarm,
        overview,
        overviewLoading,
        overviewError,
        cycleVersion,
        openCropDialog: () => setCropDialogOpen(true),
        refreshOverview,
        notifyCycleChanged,
      }}
    >
      <div className="space-y-6 sm:space-y-7">
        <PageHeader
          eyebrow={eyebrow}
          title={title}
          description={description}
          backHref={activeTab === "overview" ? "/" : "/rashkar"}
          actions={actions}
        />

        {farmsLoading ? (
          <Card>
            <CardContent className="py-12">
              <LoadingState label="Loading your registered farms..." />
            </CardContent>
          </Card>
        ) : farms.length === 0 ? (
          <Card>
            <CardContent className="py-6">
              <EmptyState
                icon={Sprout}
                title="Register a farm to start using RASHKAR"
                description="RASHKAR checks live Open-Meteo heat safety, stage-specific crop thermal thresholds, DES APY yield baselines, and extra income plans for your exact field coordinates."
                action={
                  <Button asChild>
                    <Link href="/farms/new">
                      <Plus size={16} /> Register your farm
                    </Link>
                  </Button>
                }
              />
            </CardContent>
          </Card>
        ) : !selectedFarm ? (
          <Card>
            <CardContent className="py-6">
              <EmptyState
                icon={MapPin}
                title="Select a farm"
                description="Choose one of your registered farms from the top farm selector to run RASHKAR assessments."
              />
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Active Farm & Crop Cycle Context Strip */}
            <Card className="border-[#cde0ce] bg-white">
              <CardContent className="flex flex-col gap-4 p-4 sm:p-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className="inline-flex items-center gap-2 rounded-xl bg-[#edf5ed] px-3 py-1.5 text-xs font-extrabold text-forest">
                    <MapPin size={15} className="text-leaf" />
                    {selectedFarm.name}
                  </span>

                  {(selectedFarm.taluka || selectedFarm.district) && (
                    <Badge variant="neutral">
                      {[selectedFarm.taluka, selectedFarm.district].filter(Boolean).join(", ")}
                    </Badge>
                  )}

                  {selectedFarm.calculated_area_acres != null && (
                    <Badge variant="outline">
                      {selectedFarm.calculated_area_acres.toFixed(2)} acres
                    </Badge>
                  )}

                  {selectedFarm.irrigation_type && (
                    <Badge variant="outline">
                      {formatTokenLabel(selectedFarm.irrigation_type)}
                    </Badge>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                  {overviewLoading && !overview ? (
                    <Badge variant="neutral">Checking crop cycle...</Badge>
                  ) : activeCycle ? (
                    <>
                      <span className="inline-flex items-center gap-2 rounded-full border border-[#c8e6c9] bg-[#eef7ee] px-3 py-1 text-xs font-extrabold text-forest">
                        <Sprout size={14} className="text-leaf" />
                        Active Crop: {formatCropLabel(activeCycle.crop_code)}
                        {activeCycle.variety_name ? ` · ${activeCycle.variety_name}` : ""}
                        {activeCycle.current_stage_code
                          ? ` · ${formatTokenLabel(activeCycle.current_stage_code)}`
                          : ""}
                      </span>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => setCropDialogOpen(true)}
                      >
                        Switch / Edit Crop
                      </Button>
                    </>
                  ) : (
                    <>
                      <Badge variant="orange">No active crop registered</Badge>
                      <Button
                        type="button"
                        size="sm"
                        variant="primary"
                        onClick={() => setCropDialogOpen(true)}
                      >
                        <Plus size={14} /> Register Crop
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* RASHKAR Sub-navigation Tabs */}
            <nav
              aria-label="RASHKAR modules"
              className="flex flex-wrap gap-1.5 sm:gap-2 rounded-2xl border border-line bg-[#eff5ef] p-1.5"
            >
              {RASHKAR_TABS.map((tab) => {
                const Icon = tab.icon;
                const active = activeTab === tab.key;
                return (
                  <Link
                    key={tab.key}
                    href={tab.href}
                    className={cn(
                      "inline-flex min-h-10 shrink-0 items-center gap-2 rounded-xl px-3.5 text-xs font-extrabold whitespace-nowrap transition-all sm:text-sm",
                      active
                        ? "bg-white text-forest shadow-sm"
                        : "text-muted hover:bg-white/60 hover:text-ink",
                    )}
                  >
                    <Icon size={16} className={active ? "text-leaf" : "text-[#718374]"} />
                    {tab.label}
                  </Link>
                );
              })}
            </nav>

            {children}

            <CropCycleDialog
              open={cropDialogOpen}
              onOpenChange={setCropDialogOpen}
              farmId={selectedFarm.id}
              farmName={selectedFarm.name}
              defaultAreaAcres={selectedFarm.calculated_area_acres}
              defaultIrrigation={selectedFarm.irrigation_type}
              activeCycle={activeCycle}
              onSaved={() => notifyCycleChanged()}
            />
          </>
        )}
      </div>
    </RashkarShellContext.Provider>
  );
}
