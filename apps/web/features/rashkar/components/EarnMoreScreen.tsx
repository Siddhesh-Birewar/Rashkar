"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  BookmarkCheck,
  Calculator,
  Check,
  CheckCircle2,
  CircleDollarSign,
  GitCompareArrows,
  HelpCircle,
  LoaderCircle,
  RefreshCw,
  SlidersHorizontal,
  Sparkles,
  Trash2,
} from "lucide-react";
import { ErrorState, LoadingState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { SectionHeader } from "@/components/section-header";
import { rashkarApi } from "../lib/api";
import { formatInr, formatTokenLabel } from "../lib/format";
import type {
  DiscoveredOpportunity,
  EnterpriseFinancialAnalysis,
  FarmerResourceProfile,
  OpportunityComparisonItem,
  SavedIncomePlan,
} from "../types";
import { RashkarShell, useRashkarShell } from "./RashkarShell";

const CATEGORY_TABS = [
  { key: "all", label: "All Recommended" },
  { key: "zero_cash", label: "Zero Cash" },
  { key: "very_low_cost", label: "Very Low Cost" },
  { key: "moderate_enterprise", label: "Moderate Enterprise" },
  { key: "crop_diversification", label: "Crop Diversification" },
  { key: "group_external", label: "Group / External" },
] as const;

const BUDGET_PRESETS = [
  { label: "₹0 (Zero-Cash)", value: 0 },
  { label: "₹5,000", value: 5000 },
  { label: "₹15,000", value: 15000 },
  { label: "₹40,000", value: 40000 },
  { label: "₹80,000", value: 80000 },
];

const BYPRODUCT_OPTIONS = [
  { value: "soybean_straw", label: "Soybean straw" },
  { value: "cotton_stalks", label: "Cotton stalks" },
  { value: "jowar_stover", label: "Jowar stover" },
  { value: "onion_cull", label: "Onion culls" },
  { value: "cow_dung", label: "Cow dung / manure" },
];

const ASSET_OPTIONS = [
  { value: "sprayer", label: "Power / battery sprayer" },
  { value: "pump", label: "Water pump" },
  { value: "tractor", label: "Tractor / implements" },
  { value: "drip", label: "Drip / sprinkler" },
  { value: "tools", label: "Farm tools / sieves" },
  { value: "vermicompost_pit", label: "Vermicompost pit" },
];

const QA_PROMPTS: Array<{ key: keyof NonNullable<DiscoveredOpportunity["farmer_summary_qa"]>; label: string }> = [
  { key: "what_is_it", label: "1. What is this activity?" },
  { key: "why_suits_my_farm", label: "2. Why does it fit my farm?" },
  { key: "what_will_i_need", label: "3. What resources & money will I need?" },
  { key: "how_will_i_earn_or_save", label: "4. How will I earn or save money?" },
  { key: "when_will_i_receive_money", label: "5. When will money start coming in?" },
  { key: "what_to_be_careful_about", label: "6. What should I be careful about?" },
];

const DEFAULT_PROFILE: FarmerResourceProfile = {
  available_investment_inr: 0,
  monthly_operating_budget_inr: 0,
  willing_to_borrow: false,
  available_land_acres: 0.2,
  unused_land_acres: 0.2,
  field_bunds_available: true,
  has_animal_shed: false,
  has_storage_room: false,
  has_shaded_space: false,
  water_availability: "seasonal_canal",
  water_months_available: [],
  family_labor_hours_day: 2,
  hired_labor_possible: false,
  existing_livestock: "none",
  existing_assets: [],
  crop_byproducts: [],
  byproduct_surplus_available: true,
  interests: ["open_to_suggestions"],
  has_transport: false,
  has_fpo_access: false,
  risk_tolerance: "moderate",
  category_preference: "all",
  age_range: "36-45",
  work_preference: "daily_physical",
  payback_horizon: "within_6_months",
  family_management_role: "self",
};

function EarnMoreBody() {
  const { farm, notifyCycleChanged } = useRashkarShell();

  const [profile, setProfile] = useState<FarmerResourceProfile>(DEFAULT_PROFILE);
  const [profileDrawerOpen, setProfileDrawerOpen] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileNotice, setProfileNotice] = useState<string | null>(null);

  const [opportunities, setOpportunities] = useState<DiscoveredOpportunity[]>([]);
  const [savedPlans, setSavedPlans] = useState<SavedIncomePlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [showUnmet, setShowUnmet] = useState<boolean>(false);

  // Compare state
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);
  const [compareItems, setCompareItems] = useState<OpportunityComparisonItem[]>([]);
  const [compareLoading, setCompareLoading] = useState(false);

  // Simulator modal state
  const [simOpportunity, setSimOpportunity] = useState<DiscoveredOpportunity | null>(null);
  const [simBudget, setSimBudget] = useState<string>("0");
  const [simWater, setSimWater] = useState<string>("seasonal_canal");
  const [simAnalysis, setSimAnalysis] = useState<EnterpriseFinancialAnalysis | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);
  const [planNote, setPlanNote] = useState<string>("");

  // Save/Delete feedback
  const [savingPlanId, setSavingPlanId] = useState<string | null>(null);
  const [deletingPlanId, setDeletingPlanId] = useState<string | null>(null);
  const [planBanner, setPlanBanner] = useState<string | null>(null);

  const loadWorkspace = useCallback(async () => {
    if (!farm?.id) return;
    setLoading(true);
    setError(null);
    try {
      const [prof, opps, plans] = await Promise.all([
        rashkarApi.getIncomeProfile(farm.id),
        rashkarApi.discoverOpportunities(farm.id),
        rashkarApi.listSavedPlans(farm.id),
      ]);
      setProfile(prof);
      setOpportunities(opps);
      setSavedPlans(plans);
    } catch (err: any) {
      setError(err?.message || "Failed to load extra income opportunities.");
    } finally {
      setLoading(false);
    }
  }, [farm?.id]);

  useEffect(() => {
    if (farm?.id) {
      loadWorkspace();
      setCompareIds([]);
    }
  }, [farm?.id, loadWorkspace]);

  const handleSaveProfileAndDiscover = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!farm?.id) return;
    setSavingProfile(true);
    setProfileNotice(null);
    try {
      const updated = await rashkarApi.updateIncomeProfile(farm.id, profile);
      setProfile(updated);
      const ranked = await rashkarApi.discoverOpportunities(farm.id, updated);
      setOpportunities(ranked);
      setProfileNotice("Farm resource profile saved and opportunities re-ranked.");
      setProfileDrawerOpen(false);
    } catch (err: any) {
      setProfileNotice(err?.message || "Could not update resource profile.");
    } finally {
      setSavingProfile(false);
    }
  };

  const toggleArrayValue = (field: "crop_byproducts" | "existing_assets", val: string) => {
    setProfile((prev) => {
      const current = prev[field] || [];
      const next = current.includes(val)
        ? current.filter((item) => item !== val)
        : [...current, val];
      return { ...prev, [field]: next };
    });
  };

  const filteredOpportunities = useMemo(() => {
    return opportunities.filter((item) => {
      const matchesCat = activeCategory === "all" || item.opportunity.category === activeCategory;
      const matchesFeasibility = showUnmet ? true : item.is_feasible;
      return matchesCat && matchesFeasibility;
    });
  }, [opportunities, activeCategory, showUnmet]);

  const toggleCompare = (oppId: string) => {
    setCompareIds((prev) => {
      if (prev.includes(oppId)) return prev.filter((id) => id !== oppId);
      if (prev.length >= 3) return [...prev.slice(1), oppId];
      return [...prev, oppId];
    });
  };

  const handleOpenCompare = async () => {
    if (compareIds.length < 2) return;
    setCompareOpen(true);
    setCompareLoading(true);
    try {
      const items = await rashkarApi.compareOpportunities(
        compareIds,
        Math.max(0, profile.available_investment_inr || 0),
      );
      setCompareItems(items);
    } catch {
      setCompareItems([]);
    } finally {
      setCompareLoading(false);
    }
  };

  const runSimulation = useCallback(
    async (opp: DiscoveredOpportunity, budgetNum: number, waterVal: string) => {
      if (!farm?.id) return;
      setSimLoading(true);
      setSimError(null);
      try {
        const res = await rashkarApi.calculateFarmScenario(farm.id, {
          opportunity_id: opp.opportunity.opportunity_id,
          custom_budget_inr: budgetNum,
          water_availability: waterVal,
          available_labour_hours_day: profile.family_labor_hours_day,
          available_land_acres: Math.max(profile.available_land_acres, profile.unused_land_acres),
          farm_id: farm.id,
        });
        setSimAnalysis(res);
      } catch (err: any) {
        setSimError(err?.message || "Failed to calculate 12-month financial scenario.");
      } finally {
        setSimLoading(false);
      }
    },
    [farm?.id, profile.family_labor_hours_day, profile.available_land_acres, profile.unused_land_acres],
  );

  const openSimulator = (item: DiscoveredOpportunity) => {
    const defaultBudget =
      item.opportunity.category === "zero_cash"
        ? 0
        : Math.max(
            item.opportunity.min_investment_inr,
            profile.available_investment_inr || item.opportunity.min_investment_inr,
          );
    setSimOpportunity(item);
    setSimBudget(String(defaultBudget));
    setSimWater(profile.water_availability || "seasonal_canal");
    setSimAnalysis(null);
    setPlanNote("");
    runSimulation(item, defaultBudget, profile.water_availability || "seasonal_canal");
  };

  const handleSavePlan = async (
    oppId: string,
    title: string,
    budgetInr: number,
    notes?: string,
  ) => {
    if (!farm?.id) return;
    setSavingPlanId(oppId);
    setPlanBanner(null);
    try {
      const saved = await rashkarApi.saveIncomePlan(farm.id, {
        opportunity_id: oppId,
        chosen_budget_inr: Math.max(0, budgetInr),
        notes: notes?.trim() || null,
      });
      setSavedPlans((prev) => [saved, ...prev]);
      setPlanBanner(`Saved "${title}" to ${farm.name} plans.`);
      notifyCycleChanged();
    } catch (err: any) {
      setPlanBanner(err?.message || "Could not save income plan.");
    } finally {
      setSavingPlanId(null);
    }
  };

  const handleDeletePlan = async (planId: string) => {
    if (!farm?.id) return;
    setDeletingPlanId(planId);
    try {
      await rashkarApi.deleteSavedPlan(farm.id, planId);
      setSavedPlans((prev) => prev.filter((p) => p.plan_id !== planId));
      notifyCycleChanged();
    } finally {
      setDeletingPlanId(null);
    }
  };

  if (!farm) return null;

  return (
    <div className="space-y-6">
      {/* Step 1: Resource Profile Summary Bar + Editable Drawer */}
      <Card className="border-[#cde0ce]">
        <CardContent className="space-y-4 p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="green">Step 1 · Your Farm Resources</Badge>
                <Badge variant="outline">
                  Upfront: {formatInr(profile.available_investment_inr)}
                </Badge>
                <Badge variant="outline">
                  Monthly Op: {formatInr(profile.monthly_operating_budget_inr)}
                </Badge>
                <Badge variant="outline">
                  Labor: {profile.family_labor_hours_day} hrs/day
                </Badge>
                <Badge variant="outline">
                  Water: {formatTokenLabel(profile.water_availability)}
                </Badge>
                <Badge variant="outline">
                  Spare land: {Math.max(profile.available_land_acres, profile.unused_land_acres)} ac
                </Badge>
              </div>
              <p className="text-xs text-muted">
                Opportunities below are scored using your cash budget, water, family labor, sheds,
                and crop residues. Start with ₹0 Zero-Cash options or edit your resources anytime.
              </p>
            </div>

            <Button
              type="button"
              variant={profileDrawerOpen ? "secondary" : "primary"}
              size="sm"
              onClick={() => setProfileDrawerOpen((v) => !v)}
              className="shrink-0"
            >
              <SlidersHorizontal size={15} />
              {profileDrawerOpen ? "Hide Resource Editor" : "Edit Farm Resources"}
            </Button>
          </div>

          {profileNotice && (
            <div className="rounded-xl border border-[#c8e6c9] bg-[#eef7ee] px-3.5 py-2 text-xs font-bold text-forest">
              {profileNotice}
            </div>
          )}

          {profileDrawerOpen && (
            <form
              onSubmit={handleSaveProfileAndDiscover}
              className="space-y-5 border-t border-line pt-5"
            >
              {/* Quick Investment Presets */}
              <div>
                <p className="text-xs font-extrabold text-ink">
                  Quick Upfront Cash Budget Presets
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {BUDGET_PRESETS.map((preset) => (
                    <button
                      key={preset.value}
                      type="button"
                      onClick={() =>
                        setProfile((p) => ({ ...p, available_investment_inr: preset.value }))
                      }
                      className={`min-h-9 rounded-xl border px-3 text-xs font-extrabold transition ${
                        profile.available_investment_inr === preset.value
                          ? "border-forest bg-forest text-white"
                          : "border-line bg-white text-ink hover:bg-[#f2f7f2]"
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <label className="text-xs font-extrabold text-ink">
                    Upfront Cash Available (₹)
                  </label>
                  <Input
                    type="number"
                    min="0"
                    step="500"
                    value={profile.available_investment_inr}
                    onChange={(e) =>
                      setProfile((p) => ({
                        ...p,
                        available_investment_inr: Number(e.target.value) || 0,
                      }))
                    }
                    className="mt-1.5 min-h-10 text-sm"
                  />
                </div>

                <div>
                  <label className="text-xs font-extrabold text-ink">
                    Monthly Operating Budget (₹)
                  </label>
                  <Input
                    type="number"
                    min="0"
                    step="500"
                    value={profile.monthly_operating_budget_inr}
                    onChange={(e) =>
                      setProfile((p) => ({
                        ...p,
                        monthly_operating_budget_inr: Number(e.target.value) || 0,
                      }))
                    }
                    className="mt-1.5 min-h-10 text-sm"
                  />
                </div>

                <div>
                  <label className="text-xs font-extrabold text-ink">
                    Spare Uncultivated Land (acres)
                  </label>
                  <Input
                    type="number"
                    min="0"
                    step="0.05"
                    value={profile.available_land_acres}
                    onChange={(e) => {
                      const val = Number(e.target.value) || 0;
                      setProfile((p) => ({
                        ...p,
                        available_land_acres: val,
                        unused_land_acres: val,
                      }));
                    }}
                    className="mt-1.5 min-h-10 text-sm"
                  />
                </div>

                <div>
                  <label className="text-xs font-extrabold text-ink">
                    Family Labor (hrs / day)
                  </label>
                  <Input
                    type="number"
                    min="0"
                    max="16"
                    step="0.5"
                    value={profile.family_labor_hours_day}
                    onChange={(e) =>
                      setProfile((p) => ({
                        ...p,
                        family_labor_hours_day: Math.min(16, Math.max(0, Number(e.target.value) || 0)),
                      }))
                    }
                    className="mt-1.5 min-h-10 text-sm"
                  />
                </div>

                <div>
                  <label className="text-xs font-extrabold text-ink">Water Availability</label>
                  <select
                    aria-label="Water Availability"
                    value={profile.water_availability}
                    onChange={(e) =>
                      setProfile((p) => ({ ...p, water_availability: e.target.value }))
                    }
                    className="mt-1.5 min-h-10 w-full rounded-xl border border-line bg-white px-3 text-xs font-bold text-ink"
                  >
                    <option value="reliable_year_round">Reliable year-round (Borewell/Perennial)</option>
                    <option value="seasonal_canal">Seasonal canal / post-monsoon</option>
                    <option value="limited">Limited supplemental water</option>
                    <option value="rainfed_only">Rainfed only</option>
                    <option value="none">No irrigation water</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-extrabold text-ink">Existing Livestock</label>
                  <select
                    aria-label="Existing Livestock"
                    value={profile.existing_livestock}
                    onChange={(e) =>
                      setProfile((p) => ({ ...p, existing_livestock: e.target.value }))
                    }
                    className="mt-1.5 min-h-10 w-full rounded-xl border border-line bg-white px-3 text-xs font-bold text-ink"
                  >
                    <option value="none">No livestock</option>
                    <option value="indigenous_cows">Indigenous cows / bullocks</option>
                    <option value="crossbred_cows">Crossbred / dairy cows</option>
                    <option value="goats">Goats</option>
                    <option value="desi_poultry">Desi poultry</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <label className="text-xs font-extrabold text-ink">
                    Sheds, Space & Market Access
                  </label>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    {[
                      { key: "field_bunds_available", label: "Field bunds" },
                      { key: "has_animal_shed", label: "Animal shed" },
                      { key: "has_shaded_space", label: "Shaded space" },
                      { key: "has_storage_room", label: "Storage room" },
                      { key: "has_transport", label: "Own transport" },
                      { key: "has_fpo_access", label: "FPO / Co-op member" },
                      { key: "hired_labor_possible", label: "Hired labor possible" },
                    ].map((toggle) => {
                      const checked = Boolean(profile[toggle.key as keyof FarmerResourceProfile]);
                      return (
                        <label
                          key={toggle.key}
                          className={`inline-flex cursor-pointer items-center gap-1.5 rounded-xl border px-3 py-1.5 font-semibold ${
                            checked
                              ? "border-[#b8d0ba] bg-[#eef7ee] text-forest"
                              : "border-line bg-white text-muted"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) =>
                              setProfile((p) => ({ ...p, [toggle.key]: e.target.checked }))
                            }
                            className="accent-forest"
                          />
                          {toggle.label}
                        </label>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Byproducts & Assets */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-xs font-extrabold text-ink">Available Crop Byproducts</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    {BYPRODUCT_OPTIONS.map((opt) => {
                      const active = profile.crop_byproducts.includes(opt.value);
                      return (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => toggleArrayValue("crop_byproducts", opt.value)}
                          className={`rounded-lg border px-2.5 py-1.5 font-semibold ${
                            active
                              ? "border-forest bg-[#eef7ee] text-forest"
                              : "border-line bg-white text-muted"
                          }`}
                        >
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <p className="text-xs font-extrabold text-ink">Owned Machinery / Assets</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    {ASSET_OPTIONS.map((opt) => {
                      const active = profile.existing_assets.includes(opt.value);
                      return (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => toggleArrayValue("existing_assets", opt.value)}
                          className={`rounded-lg border px-2.5 py-1.5 font-semibold ${
                            active
                              ? "border-forest bg-[#eef7ee] text-forest"
                              : "border-line bg-white text-muted"
                          }`}
                        >
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Optional Personalization */}
              <div className="rounded-2xl border border-line bg-canvas p-4 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs font-extrabold text-ink">
                    Optional Work-Style Personalization
                  </p>
                  <span className="text-[11px] font-semibold text-forest">
                    Age is used only to tailor ergonomics — never blocks or restricts opportunities.
                  </span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <label className="text-[11px] font-bold text-muted">Age Range</label>
                    <select
                      aria-label="Age Range"
                      value={profile.age_range || "36-45"}
                      onChange={(e) => setProfile((p) => ({ ...p, age_range: e.target.value }))}
                      className="mt-1 min-h-9 w-full rounded-lg border border-line bg-white px-2.5 text-xs font-semibold text-ink"
                    >
                      <option value="under_25">Under 25</option>
                      <option value="25-35">25–35</option>
                      <option value="36-45">36–45</option>
                      <option value="46-55">46–55</option>
                      <option value="56-65">56–65</option>
                      <option value="above_65">Above 65</option>
                      <option value="prefer_not_to_say">Prefer not to say</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-bold text-muted">Work Preference</label>
                    <select
                      aria-label="Work Preference"
                      value={profile.work_preference || "daily_physical"}
                      onChange={(e) =>
                        setProfile((p) => ({ ...p, work_preference: e.target.value }))
                      }
                      className="mt-1 min-h-9 w-full rounded-lg border border-line bg-white px-2.5 text-xs font-semibold text-ink"
                    >
                      <option value="daily_physical">Daily physical field work</option>
                      <option value="light_physical">Light physical work</option>
                      <option value="manage_supervise">Manage & supervise</option>
                      <option value="family_help">Family help</option>
                      <option value="hire_labor">Hire labor</option>
                      <option value="low_attention">Low daily attention</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-bold text-muted">Payback Horizon</label>
                    <select
                      aria-label="Payback Horizon"
                      value={profile.payback_horizon || "within_6_months"}
                      onChange={(e) =>
                        setProfile((p) => ({ ...p, payback_horizon: e.target.value }))
                      }
                      className="mt-1 min-h-9 w-full rounded-lg border border-line bg-white px-2.5 text-xs font-semibold text-ink"
                    >
                      <option value="few_weeks">A few weeks</option>
                      <option value="3_to_6_months">3 to 6 months</option>
                      <option value="6_to_12_months">6 to 12 months</option>
                      <option value="more_than_year">More than 1 year</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-bold text-muted">Who Will Manage It?</label>
                    <select
                      aria-label="Family Management Role"
                      value={profile.family_management_role || "self"}
                      onChange={(e) =>
                        setProfile((p) => ({ ...p, family_management_role: e.target.value }))
                      }
                      className="mt-1 min-h-9 w-full rounded-lg border border-line bg-white px-2.5 text-xs font-semibold text-ink"
                    >
                      <option value="self">Self</option>
                      <option value="family_member">Family member</option>
                      <option value="multiple_family">Multiple family members</option>
                      <option value="hired_labor">Hired labor</option>
                      <option value="fpo_group">FPO / Group</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap justify-end gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setProfileDrawerOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={savingProfile}>
                  {savingProfile ? (
                    <>
                      <LoaderCircle size={14} className="animate-spin" /> Matching...
                    </>
                  ) : (
                    <>
                      <Sparkles size={14} /> Save Profile & Match Opportunities
                    </>
                  )}
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>

      {planBanner && (
        <div className="flex items-center justify-between gap-2 rounded-xl border border-[#c8e6c9] bg-[#eef7ee] px-4 py-2.5 text-xs font-bold text-forest">
          <span>{planBanner}</span>
          <button type="button" onClick={() => setPlanBanner(null)} className="underline">
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="py-6">
            <ErrorState
              title="Could not load extra income catalog"
              description={error}
              action={
                <Button type="button" variant="secondary" onClick={loadWorkspace}>
                  <RefreshCw size={14} /> Try again
                </Button>
              }
            />
          </CardContent>
        </Card>
      )}

      {loading && opportunities.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <LoadingState label="Scoring extra income opportunities against your farm resources..." />
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Category Tabs & Excluded/Unmet Filter */}
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex gap-1.5 overflow-x-auto rounded-2xl border border-line bg-[#eff5ef] p-1">
              {CATEGORY_TABS.map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setActiveCategory(tab.key)}
                  className={`min-h-9 shrink-0 rounded-xl px-3 text-xs font-extrabold whitespace-nowrap transition ${
                    activeCategory === tab.key
                      ? "bg-white text-forest shadow-sm"
                      : "text-muted hover:text-ink"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-line bg-white px-3.5 py-2 text-xs font-bold text-ink shadow-sm">
              <input
                type="checkbox"
                checked={showUnmet}
                onChange={(e) => setShowUnmet(e.target.checked)}
                className="accent-forest"
              />
              Show options with unmet prerequisites / budget gaps
            </label>
          </div>

          {/* Compare Selected Bar */}
          {compareIds.length > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#b7d1e6] bg-[#f2f7fc] px-4 py-3 text-xs">
              <span className="font-extrabold text-[#1b4a70]">
                {compareIds.length} of 3 selected for side-by-side comparison
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => setCompareIds([])}
                >
                  Clear
                </Button>
                <Button
                  type="button"
                  size="sm"
                  disabled={compareIds.length < 2}
                  onClick={handleOpenCompare}
                >
                  <GitCompareArrows size={14} /> Compare Selected ({compareIds.length})
                </Button>
              </div>
            </div>
          )}

          {/* Opportunities Grid */}
          {filteredOpportunities.length === 0 ? (
            <Card>
              <CardContent className="space-y-3 py-8 text-center">
                <p className="text-sm font-extrabold text-ink">
                  No opportunities match this category under your current available budget /
                  resources.
                </p>
                <p className="text-xs text-muted">
                  Try toggling &ldquo;Show options with unmet prerequisites&rdquo; to see exact
                  shortfalls, or increase your budget in Edit Farm Resources.
                </p>
                {!showUnmet && (
                  <Button type="button" size="sm" variant="secondary" onClick={() => setShowUnmet(true)}>
                    Inspect Excluded Options & Shortfalls
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {filteredOpportunities.map((item) => {
                const { opportunity: opp } = item;
                const totalOutlay = opp.min_investment_inr + opp.working_capital_required_inr;
                const annualBenefit = opp.is_cost_saving
                  ? item.estimated_annual_savings_inr || opp.potential_annual_savings_inr
                  : item.estimated_annual_profit_inr || opp.potential_annual_profit_inr;
                const isSelectedCompare = compareIds.includes(opp.opportunity_id);

                return (
                  <Card
                    key={opp.opportunity_id}
                    className={!item.is_feasible ? "border-dashed border-line bg-[#fcfdfc]" : ""}
                  >
                    <CardContent className="flex h-full flex-col justify-between space-y-4 p-5">
                      <div className="space-y-3">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <Badge variant={item.is_feasible ? "green" : "orange"}>
                              Score {item.suitability_score}/100
                            </Badge>
                            <Badge variant={opp.category === "zero_cash" ? "green" : "neutral"}>
                              {formatTokenLabel(opp.category)}
                            </Badge>
                            {opp.is_cost_saving && <Badge variant="outline">Cost Saver</Badge>}
                          </div>
                          <Badge variant={item.is_feasible ? "outline" : "destructive"}>
                            {item.suitability_verdict || formatTokenLabel(item.feasibility_status)}
                          </Badge>
                        </div>

                        <div>
                          <h3 className="text-base font-extrabold text-ink">{opp.title}</h3>
                          <p className="mt-1 text-xs leading-5 text-muted">{opp.tagline}</p>
                        </div>

                        {/* Key Financial Numbers */}
                        <div className="grid grid-cols-3 gap-2 rounded-xl bg-canvas p-3 text-center">
                          <div>
                            <p className="text-[10px] font-bold text-muted">Initial Outlay</p>
                            <p className="mt-0.5 text-sm font-extrabold text-ink">
                              {formatInr(totalOutlay)}
                            </p>
                          </div>
                          <div>
                            <p className="text-[10px] font-bold text-muted">
                              {opp.is_cost_saving ? "Annual Savings" : "Annual Net Profit"}
                            </p>
                            <p className="mt-0.5 text-sm font-extrabold text-forest">
                              {formatInr(annualBenefit)}
                            </p>
                          </div>
                          <div>
                            <p className="text-[10px] font-bold text-muted">Payback</p>
                            <p className="mt-0.5 text-sm font-extrabold text-ink">
                              ~{item.payback_months} mo
                            </p>
                          </div>
                        </div>

                        {/* Why it fits */}
                        {item.matching_resources.length > 0 && (
                          <div className="space-y-1 text-xs">
                            <p className="font-extrabold text-forest">Why it fits your farm</p>
                            <ul className="space-y-1 text-ink/85">
                              {item.matching_resources.slice(0, 3).map((m, i) => (
                                <li key={i} className="flex items-start gap-1.5">
                                  <Check size={14} className="mt-0.5 shrink-0 text-leaf" />
                                  <span>{m}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Missing / Caution notes */}
                        {item.missing_requirements.length > 0 && (
                          <div className="space-y-1 rounded-xl border border-[#f3d6c4] bg-[#fff7f0] p-3 text-xs text-[#9a3700]">
                            <p className="font-extrabold">Missing / Caution Notes</p>
                            <ul className="space-y-1">
                              {item.missing_requirements.map((req, i) => (
                                <li key={i} className="flex items-start gap-1.5">
                                  <AlertCircle size={13} className="mt-0.5 shrink-0" />
                                  <span>{req}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-2 border-t border-line/70 pt-3">
                        <Button
                          type="button"
                          size="sm"
                          variant="primary"
                          onClick={() => openSimulator(item)}
                        >
                          <Calculator size={14} /> Simulate & Q&A
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant={isSelectedCompare ? "accent" : "secondary"}
                          onClick={() => toggleCompare(opp.opportunity_id)}
                        >
                          <GitCompareArrows size={14} />
                          {isSelectedCompare ? "Selected" : "Compare"}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={savingPlanId === opp.opportunity_id}
                          onClick={() =>
                            handleSavePlan(
                              opp.opportunity_id,
                              opp.title,
                              opp.category === "zero_cash" ? 0 : totalOutlay,
                            )
                          }
                        >
                          {savingPlanId === opp.opportunity_id ? (
                            "Saving..."
                          ) : (
                            <>
                              <BookmarkCheck size={14} /> Save Plan
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Saved Income Plans Section */}
      <section aria-label="Saved farm income plans">
        <SectionHeader
          title="Saved Income Plans for This Farm"
          description="Bookmarked enterprise plans persisted to your farm workspace."
        />
        {savedPlans.length === 0 ? (
          <Card>
            <CardContent className="py-6 text-center text-xs text-muted">
              No saved income plans for {farm.name} yet. Click &ldquo;Save Plan&rdquo; on any
              opportunity or inside the 12-month simulator.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-3.5 md:grid-cols-2">
            {savedPlans.map((plan) => (
              <Card key={plan.plan_id}>
                <CardContent className="flex flex-col justify-between gap-3 p-4 sm:flex-row sm:items-center">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Badge variant="green">{formatTokenLabel(plan.category)}</Badge>
                      <Badge variant="outline">Budget {formatInr(plan.chosen_budget_inr)}</Badge>
                    </div>
                    <h4 className="text-sm font-extrabold text-ink">{plan.opportunity_title}</h4>
                    <p className="text-xs text-muted">
                      Projected:{" "}
                      <strong className="text-forest">
                        {formatInr(
                          Math.max(
                            plan.projected_annual_profit_inr,
                            plan.projected_annual_savings_inr,
                          ),
                        )}
                        /yr
                      </strong>
                      {plan.payback_months != null ? ` · Payback ~${plan.payback_months} mo` : ""}
                      {" · "}Saved {plan.created_at_utc}
                    </p>
                    {plan.notes && (
                      <p className="text-[11px] italic text-muted">&ldquo;{plan.notes}&rdquo;</p>
                    )}
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    disabled={deletingPlanId === plan.plan_id}
                    onClick={() => handleDeletePlan(plan.plan_id)}
                    className="shrink-0 text-[#b71c1c] hover:bg-[#fdeeee]"
                  >
                    <Trash2 size={14} />
                    {deletingPlanId === plan.plan_id ? "Removing..." : "Delete"}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Interactive Simulator Modal */}
      <Dialog
        open={Boolean(simOpportunity)}
        onOpenChange={(open) => {
          if (!open) setSimOpportunity(null);
        }}
      >
        <DialogContent className="max-h-[90vh] max-w-3xl overflow-y-auto">
          {simOpportunity && (
            <>
              <DialogTitle className="flex items-center gap-2">
                <CircleDollarSign size={20} className="text-leaf" />
                {simOpportunity.opportunity.title}
              </DialogTitle>
              <DialogDescription>
                Plain-language Q&A, custom budget simulation, 3 financial scenarios, and 12-month
                cash-flow projection.
              </DialogDescription>

              <div className="mt-5 space-y-6">
                {/* 6 Structured Farmer Questions */}
                {simOpportunity.farmer_summary_qa && (
                  <div className="space-y-2.5">
                    <h4 className="flex items-center gap-1.5 text-xs font-extrabold uppercase tracking-wider text-forest">
                      <HelpCircle size={14} /> 6 Essential Farmer Questions
                    </h4>
                    <div className="grid gap-2.5 sm:grid-cols-2">
                      {QA_PROMPTS.map(({ key, label }) => {
                        const ans = simOpportunity.farmer_summary_qa?.[key];
                        if (!ans) return null;
                        return (
                          <div
                            key={key}
                            className="rounded-xl border border-line bg-canvas p-3 text-xs"
                          >
                            <p className="font-extrabold text-ink">{label}</p>
                            <p className="mt-1 leading-5 text-muted">{ans}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Custom Budget Simulator Controls */}
                <div className="rounded-2xl border border-[#cde0ce] bg-[#f4faf4] p-4">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div>
                      <label className="text-xs font-extrabold text-ink">
                        Custom Budget (₹)
                      </label>
                      <Input
                        type="number"
                        min="0"
                        step="500"
                        value={simBudget}
                        onChange={(e) => setSimBudget(e.target.value)}
                        className="mt-1 min-h-10 text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-extrabold text-ink">
                        Water Availability
                      </label>
                      <select
                        aria-label="Simulation Water Availability"
                        value={simWater}
                        onChange={(e) => setSimWater(e.target.value)}
                        className="mt-1 min-h-10 w-full rounded-xl border border-line bg-white px-3 text-xs font-bold text-ink"
                      >
                        <option value="reliable_year_round">Reliable year-round</option>
                        <option value="seasonal_canal">Seasonal canal</option>
                        <option value="limited">Limited</option>
                        <option value="rainfed_only">Rainfed only</option>
                      </select>
                    </div>
                    <div className="flex items-end">
                      <Button
                        type="button"
                        className="w-full"
                        disabled={simLoading}
                        onClick={() =>
                          runSimulation(simOpportunity, Number(simBudget) || 0, simWater)
                        }
                      >
                        {simLoading ? (
                          <>
                            <LoaderCircle size={15} className="animate-spin" /> Calculating...
                          </>
                        ) : (
                          <>
                            <Calculator size={15} /> Recalculate Cash Flow
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>

                {simError && (
                  <div className="rounded-xl border border-[#f2b8b5] bg-[#fdeeee] p-3 text-xs font-semibold text-[#b71c1c]">
                    {simError}
                  </div>
                )}

                {simLoading && !simAnalysis && (
                  <LoadingState label="Running NABARD & Agmarknet 3-scenario simulation..." />
                )}

                {simAnalysis && (
                  <div className="space-y-5">
                    {/* Break-Even & Key Totals Callout */}
                    <div className="grid gap-3 sm:grid-cols-4">
                      <div className="rounded-xl border border-line bg-white p-3">
                        <p className="text-[11px] font-bold text-muted">Initial Outlay</p>
                        <p className="mt-0.5 text-base font-extrabold text-ink">
                          {formatInr(simAnalysis.total_initial_outlay_inr)}
                        </p>
                      </div>
                      <div className="rounded-xl border border-[#cde0ce] bg-[#eef7ee] p-3">
                        <p className="text-[11px] font-bold text-forest">
                          {simAnalysis.is_cost_saving ? "Annual Savings" : "Cash Operating Surplus"}
                        </p>
                        <p className="mt-0.5 text-base font-extrabold text-forest">
                          {formatInr(
                            simAnalysis.is_cost_saving
                              ? simAnalysis.calculated_annual_savings_inr
                              : simAnalysis.cash_operating_surplus_inr,
                          )}
                        </p>
                      </div>
                      <div className="rounded-xl border border-line bg-white p-3">
                        <p className="text-[11px] font-bold text-muted">Break-Even</p>
                        <p className="mt-0.5 text-base font-extrabold text-ink">
                          {simAnalysis.calculated_break_even_months != null
                            ? `${simAnalysis.calculated_break_even_months} months`
                            : "Beyond 24 mo"}
                        </p>
                      </div>
                      <div className="rounded-xl border border-line bg-white p-3">
                        <p className="text-[11px] font-bold text-muted">Economic Profit</p>
                        <p className="mt-0.5 text-base font-extrabold text-ink">
                          {formatInr(simAnalysis.economic_profit_inr)}
                        </p>
                      </div>
                    </div>

                    {/* Conservative / Realistic / Optimistic Scenarios */}
                    <div className="grid gap-3 sm:grid-cols-3">
                      {(["conservative", "base", "optimistic"] as const).map((key) => {
                        const sc = simAnalysis.scenarios?.[key];
                        if (!sc) return null;
                        const label =
                          key === "base"
                            ? "Realistic (Base)"
                            : key === "conservative"
                              ? "Conservative"
                              : "Optimistic";
                        return (
                          <div
                            key={key}
                            className={`rounded-2xl border p-3.5 text-xs ${
                              key === "base"
                                ? "border-[#b8d0ba] bg-[#f4faf4]"
                                : "border-line bg-white"
                            }`}
                          >
                            <p className="font-extrabold text-ink">{label}</p>
                            <p className="mt-0.5 text-[11px] text-muted">{sc.price_assumption}</p>
                            <div className="mt-3 space-y-1">
                              <div className="flex justify-between">
                                <span className="text-muted">Gross + Saved:</span>
                                <span className="font-bold text-ink">
                                  {formatInr(sc.gross_annual_revenue_inr + sc.annual_money_saved_inr)}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted">Annual Opex:</span>
                                <span className="font-bold text-ink">
                                  {formatInr(sc.annual_opex_inr)}
                                </span>
                              </div>
                              <div className="flex justify-between border-t border-line pt-1">
                                <span className="font-extrabold text-forest">Net Annual:</span>
                                <span className="font-extrabold text-forest">
                                  {formatInr(sc.net_annual_profit_inr)}
                                </span>
                              </div>
                              <div className="flex justify-between text-[11px]">
                                <span className="text-muted">Break-even:</span>
                                <span className="font-bold text-ink">
                                  {sc.break_even_months != null
                                    ? `${sc.break_even_months} mo`
                                    : "N/A"}
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* 12-Month Cash-Flow Visual Bar Chart + Table */}
                    {simAnalysis.monthly_cash_flows?.length > 0 && (
                      <div className="rounded-2xl border border-line bg-white p-4 space-y-3">
                        <p className="text-xs font-extrabold text-ink">
                          12-Month Net Cash-Flow Projection (Base Scenario)
                        </p>
                        {(() => {
                          const maxAbs = Math.max(
                            1,
                            ...simAnalysis.monthly_cash_flows.map((v) => Math.abs(v)),
                          );
                          let cumulative = 0;
                          return (
                            <>
                              <div className="grid grid-cols-12 items-end gap-1.5 h-28 pt-2">
                                {simAnalysis.monthly_cash_flows.map((val, idx) => {
                                  const heightPct = Math.max(8, Math.round((Math.abs(val) / maxAbs) * 100));
                                  const positive = val >= 0;
                                  return (
                                    <div
                                      key={idx}
                                      className="flex h-full flex-col items-center justify-end gap-1"
                                      title={`Month ${idx + 1}: ${formatInr(val)}`}
                                    >
                                      <div
                                        style={{ height: `${heightPct}%` }}
                                        className={`w-full rounded-t-md ${
                                          positive ? "bg-leaf" : "bg-accent"
                                        }`}
                                      />
                                      <span className="text-[10px] font-bold text-muted">
                                        M{idx + 1}
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                              <div className="overflow-x-auto">
                                <table className="w-full min-w-[540px] text-left text-[11px]">
                                  <thead>
                                    <tr className="border-b border-line text-muted">
                                      <th className="py-1.5 pr-2">Month</th>
                                      <th className="py-1.5 pr-2">Monthly Net Flow</th>
                                      <th className="py-1.5">Cumulative Balance</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-line/60">
                                    {simAnalysis.monthly_cash_flows.map((val, idx) => {
                                      cumulative += val;
                                      return (
                                        <tr key={idx}>
                                          <td className="py-1 pr-2 font-bold text-ink">
                                            Month {idx + 1}
                                          </td>
                                          <td
                                            className={`py-1 pr-2 font-bold ${
                                              val >= 0 ? "text-forest" : "text-accent"
                                            }`}
                                          >
                                            {val < 0 ? `-${formatInr(Math.abs(val))}` : formatInr(val)}
                                          </td>
                                          <td
                                            className={`py-1 font-bold ${
                                              cumulative >= 0 ? "text-forest" : "text-muted"
                                            }`}
                                          >
                                            {cumulative < 0
                                              ? `-${formatInr(Math.abs(cumulative))}`
                                              : formatInr(cumulative)}
                                          </td>
                                        </tr>
                                      );
                                    })}
                                  </tbody>
                                </table>
                              </div>
                            </>
                          );
                        })()}
                      </div>
                    )}

                    {/* Disclaimer & Save Action */}
                    <div className="space-y-3 rounded-2xl border border-line bg-canvas p-4 text-xs">
                      <p className="text-[11px] leading-5 text-muted">
                        <strong className="text-ink">Source:</strong>{" "}
                        {simAnalysis.nabard_source_citation || simAnalysis.source_attribution}
                        <br />
                        {simAnalysis.disclaimer}
                      </p>
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                        <Input
                          value={planNote}
                          onChange={(e) => setPlanNote(e.target.value)}
                          placeholder="Optional personal note (e.g., Try after Kharif harvest)"
                          className="min-h-10 flex-1 text-xs"
                        />
                        <Button
                          type="button"
                          disabled={savingPlanId === simAnalysis.opportunity_id}
                          onClick={async () => {
                            await handleSavePlan(
                              simAnalysis.opportunity_id,
                              simAnalysis.opportunity_title,
                              Number(simBudget) || 0,
                              planNote,
                            );
                            setSimOpportunity(null);
                          }}
                        >
                          <CheckCircle2 size={15} />
                          {savingPlanId === simAnalysis.opportunity_id
                            ? "Saving..."
                            : "Save Plan to Farm"}
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Side-by-Side Comparison Modal */}
      <Dialog open={compareOpen} onOpenChange={setCompareOpen}>
        <DialogContent className="max-h-[90vh] max-w-3xl overflow-y-auto">
          <DialogTitle className="flex items-center gap-2">
            <GitCompareArrows size={20} className="text-calm" />
            Side-by-Side Opportunity Comparison
          </DialogTitle>
          <DialogDescription>
            Comparing selected opportunities under uniform NABARD & Agmarknet assumptions.
          </DialogDescription>

          {compareLoading ? (
            <div className="py-10">
              <LoadingState label="Comparing financial assumptions..." />
            </div>
          ) : compareItems.length === 0 ? (
            <p className="py-6 text-xs text-muted">No comparison items returned.</p>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-xs">
                <thead>
                  <tr className="border-b border-line text-[11px] font-extrabold uppercase tracking-wider text-muted">
                    <th className="py-2 pr-3">Metric</th>
                    {compareItems.map((item) => (
                      <th key={item.opportunity_id} className="py-2 pr-3 text-ink">
                        {item.title}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/60">
                  <tr>
                    <td className="py-2.5 pr-3 font-bold text-muted">Category</td>
                    {compareItems.map((item) => (
                      <td key={item.opportunity_id} className="py-2.5 pr-3 font-semibold">
                        {formatTokenLabel(item.category)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-bold text-muted">Initial Outlay</td>
                    {compareItems.map((item) => (
                      <td key={item.opportunity_id} className="py-2.5 pr-3 font-extrabold text-ink">
                        {formatInr(item.initial_investment_inr)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-bold text-muted">Annual Profit / Savings</td>
                    {compareItems.map((item) => (
                      <td
                        key={item.opportunity_id}
                        className="py-2.5 pr-3 font-extrabold text-forest"
                      >
                        {formatInr(
                          Math.max(item.net_annual_profit_inr, item.annual_money_saved_inr),
                        )}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-bold text-muted">Payback</td>
                    {compareItems.map((item) => (
                      <td key={item.opportunity_id} className="py-2.5 pr-3">
                        {item.payback_months != null ? `${item.payback_months} months` : "N/A"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-bold text-muted">Daily Labor</td>
                    {compareItems.map((item) => (
                      <td key={item.opportunity_id} className="py-2.5 pr-3">
                        {item.daily_labor_hours} hrs/day
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-bold text-muted">Land / Water</td>
                    {compareItems.map((item) => (
                      <td key={item.opportunity_id} className="py-2.5 pr-3 text-muted">
                        {item.land_required_acres} ac · {formatTokenLabel(item.water_needs)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-bold text-muted">Risk Level</td>
                    {compareItems.map((item) => (
                      <td key={item.opportunity_id} className="py-2.5 pr-3">
                        <Badge variant="neutral">{formatTokenLabel(item.risk_level)}</Badge>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function EarnMoreScreen() {
  return (
    <RashkarShell
      activeTab="earn-more"
      eyebrow="RASHKAR · Earn More"
      title="What extra income can my farm earn?"
      description="Personalized cost-saving and enterprise diversification options starting at ₹0, with 12-month cash-flow simulation and saved farm plans."
    >
      <EarnMoreBody />
    </RashkarShell>
  );
}
