"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, LoaderCircle, Sprout } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { rashkarApi } from "../lib/api";
import { formatCropLabel, formatTokenLabel } from "../lib/format";
import type { RashkarCanonicalCropItem, RashkarCropCycle } from "../types";

interface CropCycleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  farmId: string;
  farmName?: string;
  defaultAreaAcres?: number | null;
  defaultIrrigation?: string | null;
  activeCycle?: RashkarCropCycle | null;
  onSaved?: (cycle: RashkarCropCycle) => void;
}

const SEASON_OPTIONS = [
  { value: "kharif", label: "Kharif (Monsoon)" },
  { value: "rabi", label: "Rabi (Winter)" },
  { value: "summer", label: "Summer" },
  { value: "perennial", label: "Perennial / Annual" },
];

const IRRIGATION_OPTIONS = [
  { value: "drip", label: "Drip irrigation" },
  { value: "sprinkler", label: "Sprinkler" },
  { value: "furrow", label: "Furrow / Channel" },
  { value: "flood", label: "Flood / Basin" },
  { value: "canal", label: "Seasonal canal" },
  { value: "borewell", label: "Borewell / Well" },
  { value: "rainfed", label: "Rainfed (no supplemental irrigation)" },
];

export function CropCycleDialog({
  open,
  onOpenChange,
  farmId,
  farmName,
  defaultAreaAcres,
  defaultIrrigation,
  activeCycle,
  onSaved,
}: CropCycleDialogProps) {
  const [crops, setCrops] = useState<RashkarCanonicalCropItem[]>([]);
  const [existingCycles, setExistingCycles] = useState<RashkarCropCycle[]>([]);
  const [loadingCatalog, setLoadingCatalog] = useState(false);

  const [cropCode, setCropCode] = useState<string>(activeCycle?.crop_code || "soybean");
  const [varietyName, setVarietyName] = useState<string>(activeCycle?.variety_name || "");
  const [sowingDate, setSowingDate] = useState<string>(activeCycle?.sowing_date || "");
  const [season, setSeason] = useState<string>(activeCycle?.season || "kharif");
  const [areaAcres, setAreaAcres] = useState<string>(
    activeCycle?.planted_area_acres != null
      ? String(activeCycle.planted_area_acres)
      : defaultAreaAcres != null
        ? String(defaultAreaAcres)
        : "",
  );
  const [irrigationType, setIrrigationType] = useState<string>(
    activeCycle?.irrigation_type || defaultIrrigation || "rainfed",
  );
  const [stageCode, setStageCode] = useState<string>(activeCycle?.current_stage_code || "");

  const [submitting, setSubmitting] = useState(false);
  const [activatingId, setActivatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !farmId) return;

    setError(null);
    setCropCode(activeCycle?.crop_code || "soybean");
    setVarietyName(activeCycle?.variety_name || "");
    setSowingDate(activeCycle?.sowing_date || "");
    setSeason(activeCycle?.season || "kharif");
    setAreaAcres(
      activeCycle?.planted_area_acres != null
        ? String(activeCycle.planted_area_acres)
        : defaultAreaAcres != null
          ? String(defaultAreaAcres)
          : "",
    );
    setIrrigationType(activeCycle?.irrigation_type || defaultIrrigation || "rainfed");
    setStageCode(activeCycle?.current_stage_code || "");

    let mounted = true;
    async function loadMeta() {
      setLoadingCatalog(true);
      try {
        const [cropList, cycleList] = await Promise.all([
          rashkarApi.listCrops(true),
          rashkarApi.listCropCycles(farmId),
        ]);
        if (!mounted) return;
        setCrops(cropList);
        setExistingCycles(cycleList);
        if (!activeCycle && cropList.length > 0 && !cropList.some((c) => c.crop_code === cropCode)) {
          setCropCode(cropList[0].crop_code);
          setSeason(cropList[0].standard_season || "kharif");
        }
      } catch (err: any) {
        if (!mounted) return;
        setError(err?.message || "Failed to load canonical crops list.");
      } finally {
        if (mounted) setLoadingCatalog(false);
      }
    }

    loadMeta();
    return () => {
      mounted = false;
    };
  }, [open, farmId, activeCycle?.id]);

  const selectedCrop = useMemo(
    () => crops.find((c) => c.crop_code === cropCode),
    [crops, cropCode],
  );

  const handleCropChange = (nextCode: string) => {
    setCropCode(nextCode);
    setStageCode("");
    const found = crops.find((c) => c.crop_code === nextCode);
    if (found?.standard_season) {
      setSeason(found.standard_season);
    }
  };

  const handleSubmitNew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cropCode.trim()) {
      setError("Please select a crop.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const parsedArea = areaAcres.trim() ? Number(areaAcres) : null;
      const saved = await rashkarApi.upsertActiveCropCycle(farmId, {
        crop_code: cropCode,
        variety_name: varietyName.trim() || null,
        sowing_date: sowingDate.trim() || null,
        season: season || null,
        planted_area_acres:
          parsedArea !== null && Number.isFinite(parsedArea) && parsedArea >= 0 ? parsedArea : null,
        irrigation_type: irrigationType || null,
        current_stage_code: stageCode.trim() || null,
        stage_source: stageCode.trim() ? "farmer_confirmed" : "estimated_from_das",
        stage_confidence: stageCode.trim() ? 1.0 : null,
        is_active: true,
      });
      onSaved?.(saved);
      onOpenChange(false);
    } catch (err: any) {
      setError(err?.message || "Could not save crop cycle.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleActivateExisting = async (cycle: RashkarCropCycle) => {
    setActivatingId(cycle.id);
    setError(null);
    try {
      const updated = await rashkarApi.updateCropCycle(farmId, cycle.id, { is_active: true });
      onSaved?.(updated);
      onOpenChange(false);
    } catch (err: any) {
      setError(err?.message || "Could not switch active crop cycle.");
    } finally {
      setActivatingId(null);
    }
  };

  const inactiveCycles = existingCycles.filter((c) => !c.is_active);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-xl overflow-y-auto">
        <DialogTitle className="flex items-center gap-2">
          <Sprout size={20} className="text-leaf" />
          {activeCycle ? "Register or Switch Active Crop" : "Register Active Crop Cycle"}
        </DialogTitle>
        <DialogDescription>
          {farmName ? `Farm: ${farmName}. ` : ""}
          RASHKAR never assumes a hidden default crop — register the crop currently growing on this
          plot so heat stress and yield screening reflect real field phenology.
        </DialogDescription>

        {error && (
          <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-[#f2b8b5] bg-[#fdeeee] p-3 text-xs font-semibold text-[#b71c1c]">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loadingCatalog ? (
          <div className="flex items-center justify-center gap-2 py-10 text-sm text-muted">
            <LoaderCircle size={18} className="animate-spin text-leaf" />
            Loading canonical crop catalogue...
          </div>
        ) : (
          <form onSubmit={handleSubmitNew} className="mt-5 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="text-xs font-extrabold text-ink">Crop *</label>
                <select
                  aria-label="Select Crop"
                  value={cropCode}
                  onChange={(e) => handleCropChange(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-white px-3.5 text-sm font-semibold text-ink shadow-sm focus:border-leaf focus:outline-none"
                >
                  {crops.length > 0 ? (
                    crops.map((crop) => (
                      <option key={crop.crop_code} value={crop.crop_code}>
                        {crop.common_name_en} ({crop.common_name_mr}) — {crop.standard_season}
                        {crop.is_pioneer_pilot_crop ? " ★" : ""}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="soybean">Soybean (सोयाबीन)</option>
                      <option value="cotton">Cotton (कापूस)</option>
                      <option value="jowar">Jowar / Sorghum (ज्वारी)</option>
                      <option value="sugarcane">Sugarcane (ऊस)</option>
                      <option value="onion">Onion (कांदा)</option>
                      <option value="wheat">Wheat (गहू)</option>
                      <option value="gram">Gram / Chickpea (हरभरा)</option>
                      <option value="tur">Tur / Pigeon Pea (तूर)</option>
                    </>
                  )}
                </select>
                {selectedCrop && (
                  <p className="mt-1 text-[11px] text-muted">
                    Botanical: <em>{selectedCrop.botanical_name}</em> · Coverage:{" "}
                    {formatTokenLabel(selectedCrop.support_level)}
                  </p>
                )}
              </div>

              <div>
                <label className="text-xs font-extrabold text-ink">Variety (optional)</label>
                <Input
                  value={varietyName}
                  onChange={(e) => setVarietyName(e.target.value)}
                  placeholder="e.g., JS-335, NHH-44, Bhima Shakti"
                  className="mt-1.5 min-h-11 text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-extrabold text-ink">Sowing date</label>
                <Input
                  type="date"
                  value={sowingDate}
                  onChange={(e) => setSowingDate(e.target.value)}
                  className="mt-1.5 min-h-11 text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-extrabold text-ink">Season</label>
                <select
                  aria-label="Season"
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-white px-3 text-sm font-semibold text-ink shadow-sm focus:border-leaf focus:outline-none"
                >
                  {SEASON_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-extrabold text-ink">Planted area (acres)</label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={areaAcres}
                  onChange={(e) => setAreaAcres(e.target.value)}
                  placeholder="e.g., 2.5"
                  className="mt-1.5 min-h-11 text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-extrabold text-ink">Irrigation method</label>
                <select
                  aria-label="Irrigation method"
                  value={irrigationType}
                  onChange={(e) => setIrrigationType(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-white px-3 text-sm font-semibold text-ink shadow-sm focus:border-leaf focus:outline-none"
                >
                  {IRRIGATION_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-extrabold text-ink">
                  Growth stage (optional)
                </label>
                <select
                  aria-label="Current growth stage"
                  value={stageCode}
                  onChange={(e) => setStageCode(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-white px-3 text-sm font-semibold text-ink shadow-sm focus:border-leaf focus:outline-none"
                >
                  <option value="">Auto-estimate from sowing date</option>
                  {(selectedCrop?.stages || []).map((st) => (
                    <option key={st.stage_code} value={st.stage_code}>
                      {st.stage_name_en}
                      {st.stage_name_mr ? ` (${st.stage_name_mr})` : ""}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2 border-t border-line pt-4">
              <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? (
                  <>
                    <LoaderCircle size={16} className="animate-spin" /> Saving...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={16} /> Save Active Crop
                  </>
                )}
              </Button>
            </div>
          </form>
        )}

        {inactiveCycles.length > 0 && (
          <div className="mt-6 border-t border-line pt-4">
            <p className="text-xs font-extrabold uppercase tracking-wider text-muted">
              Previously Registered Cycles on This Farm
            </p>
            <div className="mt-2.5 space-y-2">
              {inactiveCycles.slice(0, 5).map((cycle) => (
                <div
                  key={cycle.id}
                  className="flex items-center justify-between gap-3 rounded-xl border border-line bg-canvas px-3.5 py-2.5"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-ink">
                        {formatCropLabel(cycle.crop_code)}
                      </span>
                      {cycle.variety_name && (
                        <Badge variant="neutral">{cycle.variety_name}</Badge>
                      )}
                      {cycle.season && (
                        <Badge variant="outline" className="text-[10px]">
                          {formatTokenLabel(cycle.season)}
                        </Badge>
                      )}
                    </div>
                    <p className="mt-0.5 text-[11px] text-muted">
                      {cycle.sowing_date ? `Sown ${cycle.sowing_date}` : "No sowing date"}
                      {cycle.current_stage_code
                        ? ` · Stage: ${formatTokenLabel(cycle.current_stage_code)}`
                        : ""}
                    </p>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    disabled={activatingId === cycle.id}
                    onClick={() => handleActivateExisting(cycle)}
                  >
                    {activatingId === cycle.id ? "Switching..." : "Make Active"}
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
