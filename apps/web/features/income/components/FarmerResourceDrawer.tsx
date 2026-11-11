"use client";

import { useState } from "react";
import { X, Check, SlidersHorizontal, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { FarmResourceProfile } from "../types";

interface FarmerResourceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  profile: FarmResourceProfile | null;
  totalFarmAcres: number;
  onSaveProfile: (updated: Partial<FarmResourceProfile>) => Promise<void>;
}

const BUDGET_PRESETS = [0, 10000, 25000, 50000, 100000, 250000];
const WATER_OPTIONS = [
  { value: "reliable_year_round", label: "Reliable Year-Round (Perennial Well / Canal)" },
  { value: "seasonal_canal", label: "Seasonal Canal / Shared Well (5-8 Months)" },
  { value: "farm_pond", label: "Farm Pond (Shet Tale with Rain Catchment)" },
  { value: "limited", label: "Limited Water (Borewell with Low Discharge)" },
  { value: "rainfed_only", label: "Rainfed Only (Monsoon Dependency)" },
];

export function FarmerResourceDrawer({
  isOpen,
  onClose,
  profile,
  totalFarmAcres,
  onSaveProfile,
}: FarmerResourceDrawerProps) {
  const [acres, setAcres] = useState<number>(profile?.available_diversification_acres ?? 0.5);
  const [budget, setBudget] = useState<number>(profile?.available_investment_inr ?? 0);
  const [water, setWater] = useState<string>(profile?.water_source ?? "seasonal_canal");
  const [familyHours, setFamilyHours] = useState<number>(profile?.family_labor_hours_day ?? 2.0);
  const [hasElec, setHasElec] = useState<boolean>(true);
  const [elecType, setElecType] = useState<string>("single_phase");
  const [hasShed, setHasShed] = useState<boolean>(profile?.has_animal_shed ?? false);
  const [hasStorage, setHasStorage] = useState<boolean>(profile?.has_storage_room ?? false);
  const [hasPond, setHasPond] = useState<boolean>(profile?.has_farm_pond ?? false);
  const [isSaving, setIsSaving] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await onSaveProfile({
        available_diversification_acres: acres,
        available_investment_inr: budget,
        water_source: water,
        family_labor_hours_day: familyHours,
        has_animal_shed: hasShed,
        has_storage_room: hasStorage,
        has_farm_pond: hasPond,
        existing_equipment: hasElec ? ["sprayer", "pump"] : ["sprayer"],
        existing_livestock: hasShed ? ["indigenous_cows"] : [],
      });
      onClose();
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="relative max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-3xl border border-line bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-line pb-4">
          <div className="flex items-center gap-2">
            <span className="flex size-8 items-center justify-center rounded-lg bg-[#edf5ed] text-forest">
              <SlidersHorizontal size={16} />
            </span>
            <div>
              <h2 className="text-lg font-extrabold text-ink">Farm Resource Profile</h2>
              <p className="text-xs text-muted">Tailor diversification matching to your actual farm assets</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-muted hover:bg-canvas hover:text-ink"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-5 text-xs">
          {/* 1. Land Allocation */}
          <div>
            <div className="flex items-center justify-between">
              <label className="font-bold text-ink">
                Area Available for Diversification (Acres)
              </label>
              <span className="font-extrabold text-forest">{acres} acres</span>
            </div>
            <p className="mt-0.5 text-[11px] text-muted">
              You do not need to use your entire farm ({totalFarmAcres ? `${totalFarmAcres.toFixed(1)} ac total` : "field"}).
              Select what portion you can safely allocate.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {[0.1, 0.25, 0.5, 1.0, 2.0, 5.0].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setAcres(val)}
                  className={`rounded-xl border px-3 py-1.5 font-bold transition-all ${
                    acres === val
                      ? "border-forest bg-forest text-white"
                      : "border-line bg-white text-ink hover:bg-canvas"
                  }`}
                >
                  {val} ac
                </button>
              ))}
            </div>
          </div>

          {/* 2. Budget Input */}
          <div>
            <div className="flex items-center justify-between">
              <label className="font-bold text-ink">
                Upfront Investment Budget (₹)
              </label>
              <span className="font-extrabold text-forest">
                {budget === 0 ? "₹0 (Zero Cash)" : `₹${budget.toLocaleString("en-IN")}`}
              </span>
            </div>
            <p className="mt-0.5 text-[11px] text-muted">
              Zero cash is fully supported! We will match opportunities that use existing residues or peer sharing.
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {BUDGET_PRESETS.map((b) => (
                <button
                  key={b}
                  type="button"
                  onClick={() => setBudget(b)}
                  className={`rounded-xl border px-3 py-1.5 font-bold transition-all ${
                    budget === b
                      ? "border-forest bg-forest text-white"
                      : "border-line bg-white text-ink hover:bg-canvas"
                  }`}
                >
                  {b === 0 ? "₹0 (Zero)" : `₹${(b / 1000).toFixed(0)}k`}
                </button>
              ))}
            </div>
          </div>

          {/* 3. Water Source */}
          <div>
            <label className="font-bold text-ink">Water Availability</label>
            <select
              value={water}
              onChange={(e) => {
                setWater(e.target.value);
                if (e.target.value === "farm_pond") setHasPond(true);
              }}
              className="mt-1.5 w-full rounded-xl border border-line bg-canvas p-2.5 font-medium text-ink focus:border-forest focus:outline-none"
            >
              {WATER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* 4. Family Labour */}
          <div>
            <div className="flex items-center justify-between">
              <label className="font-bold text-ink">Family Labour Available Daily</label>
              <span className="font-extrabold text-forest">{familyHours} hrs/day</span>
            </div>
            <div className="mt-2 flex gap-2">
              {[1.0, 2.0, 3.0, 4.0, 6.0].map((h) => (
                <button
                  key={h}
                  type="button"
                  onClick={() => setFamilyHours(h)}
                  className={`flex-1 rounded-xl border py-1.5 font-bold text-center transition-all ${
                    familyHours === h
                      ? "border-forest bg-forest text-white"
                      : "border-line bg-white text-ink hover:bg-canvas"
                  }`}
                >
                  {h}h
                </button>
              ))}
            </div>
          </div>

          {/* 5. Infrastructure Checkboxes */}
          <div className="rounded-2xl border border-line bg-canvas p-3.5 space-y-2.5">
            <span className="font-bold text-ink block text-[11px] uppercase tracking-wider text-muted">
              Existing Farm Infrastructure
            </span>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hasShed}
                  onChange={(e) => setHasShed(e.target.checked)}
                  className="rounded border-line text-forest focus:ring-forest"
                />
                <span className="text-ink font-medium">Animal / Cattle Shed</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hasPond}
                  onChange={(e) => setHasPond(e.target.checked)}
                  className="rounded border-line text-forest focus:ring-forest"
                />
                <span className="text-ink font-medium">Farm Pond (Shet Tale)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hasStorage}
                  onChange={(e) => setHasStorage(e.target.checked)}
                  className="rounded border-line text-forest focus:ring-forest"
                />
                <span className="text-ink font-medium">Covered Storage Room</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hasElec}
                  onChange={(e) => setHasElec(e.target.checked)}
                  className="rounded border-line text-forest focus:ring-forest"
                />
                <span className="text-ink font-medium">Farm Electricity Grid</span>
              </label>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-line pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isSaving}>
              {isSaving ? "Updating Matches..." : "Save Profile & Update Matches"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
