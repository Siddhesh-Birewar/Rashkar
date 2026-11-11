"use client";

import { CircleDollarSign, SlidersHorizontal, MapPin, Droplets, Sprout } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BackButton } from "@/components/back-button";
import type { FarmResourceProfile } from "../types";

interface IncomeHeaderProps {
  farmName?: string;
  totalAcres?: number;
  profile?: FarmResourceProfile | null;
  onOpenProfileDrawer: () => void;
}

export function IncomeHeader({
  farmName = "My Farm",
  totalAcres,
  profile,
  onOpenProfileDrawer,
}: IncomeHeaderProps) {
  const allocatedAcres = profile?.available_diversification_acres ?? 0.5;
  const budget = profile?.available_investment_inr ?? 0;
  const water = profile?.water_source?.replace("_", " ") ?? "seasonal canal";

  return (
    <div className="rounded-2xl border border-line bg-gradient-to-br from-white via-[#f8faf8] to-[#edf5ed] p-5 shadow-sm sm:p-7">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex items-start gap-3">
          <BackButton fallbackHref="/" className="mt-1" />
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="inline-flex size-9 items-center justify-center rounded-xl bg-forest text-white shadow-sm">
                <CircleDollarSign size={20} />
              </span>
              <Badge variant="green" className="font-extrabold uppercase tracking-wider text-[10px]">
                Diversification Advisory
              </Badge>
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
              Farm Income Diversification
            </h1>
            <p className="max-w-2xl text-xs text-muted sm:text-sm">
              Discover new ways to earn from the land, water, crop residue, and farm assets you already
              have — with realistic, evidence-backed financial models and zero fabricated returns.
            </p>
          </div>
        </div>

        <Button
          type="button"
          onClick={onOpenProfileDrawer}
          variant="secondary"
          className="shrink-0 rounded-xl border-line bg-white shadow-sm hover:bg-[#f3f8f3]"
        >
          <SlidersHorizontal size={15} className="text-leaf" />
          Edit Resource Profile
        </Button>
      </div>

      {/* Farm Context Snapshot Bar */}
      <div className="mt-5 grid grid-cols-2 gap-2 border-t border-line/80 pt-4 sm:grid-cols-4 sm:gap-3 text-xs">
        <div className="flex items-center gap-2.5 rounded-xl border border-line/60 bg-white/80 p-2.5">
          <MapPin size={16} className="text-leaf shrink-0" />
          <div className="min-w-0">
            <span className="block text-[10px] font-bold text-muted uppercase">Selected Farm</span>
            <span className="truncate font-extrabold text-ink block">{farmName}</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-xl border border-line/60 bg-white/80 p-2.5">
          <Sprout size={16} className="text-soil shrink-0" />
          <div className="min-w-0">
            <span className="block text-[10px] font-bold text-muted uppercase">Allocated Space</span>
            <span className="font-extrabold text-ink block">
              {allocatedAcres} ac{" "}
              <span className="text-[10px] font-normal text-muted">
                ({totalAcres ? `of ${totalAcres.toFixed(1)} ac` : "field"})
              </span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-xl border border-line/60 bg-white/80 p-2.5">
          <CircleDollarSign size={16} className="text-forest shrink-0" />
          <div className="min-w-0">
            <span className="block text-[10px] font-bold text-muted uppercase">Starting Budget</span>
            <span className="font-extrabold text-ink block">
              {budget === 0 ? "₹0 (Zero-Cash)" : `₹${budget.toLocaleString("en-IN")}`}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-xl border border-line/60 bg-white/80 p-2.5">
          <Droplets size={16} className="text-calm shrink-0" />
          <div className="min-w-0">
            <span className="block text-[10px] font-bold text-muted uppercase">Water Source</span>
            <span className="truncate font-extrabold text-ink capitalize block">{water}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
