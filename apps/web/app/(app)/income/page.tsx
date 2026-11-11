"use client";

import { useEffect, useState, useMemo } from "react";
import {
  Lightbulb,
  Calculator,
  GitCompareArrows,
  FileCheck2,
  Search,
  Filter,
  CheckCircle2,
  Sparkles,
  Layers,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useFarm } from "@/lib/farm-context";
import { incomeApi } from "@/features/income/lib/api";
import { IncomeHeader } from "@/features/income/components/IncomeHeader";
import { FarmerResourceDrawer } from "@/features/income/components/FarmerResourceDrawer";
import { OpportunityCard } from "@/features/income/components/OpportunityCard";
import { OpportunityDetailModal } from "@/features/income/components/OpportunityDetailModal";
import { ScenarioCalculator } from "@/features/income/components/ScenarioCalculator";
import { OpportunityCompareModal } from "@/features/income/components/OpportunityCompareModal";
import { SavedPlansView } from "@/features/income/components/SavedPlansView";
import type {
  DetailedOpportunity,
  FarmResourceProfile,
  OpportunityCategory,
  SavedPlan,
} from "@/features/income/types";

export default function IncomePage() {
  const { selectedFarm, selectedFarmId, farms } = useFarm();
  const currentFarm = selectedFarm || (farms.length > 0 ? farms[0] : null);
  const farmId = currentFarm?.id || "default_farm";

  // Tab State
  const [activeTab, setActiveTab] = useState<"catalog" | "calculator" | "plans">("catalog");

  // Data State
  const [categories, setCategories] = useState<OpportunityCategory[]>([]);
  const [opportunities, setOpportunities] = useState<DetailedOpportunity[]>([]);
  const [profile, setProfile] = useState<FarmResourceProfile | null>(null);
  const [savedPlans, setSavedPlans] = useState<SavedPlan[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters State
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedBudgetTier, setSelectedBudgetTier] = useState<string>("all");
  const [selectedWaterFilter, setSelectedWaterFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modals & Interactive State
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [exploredOpp, setExploredOpp] = useState<DetailedOpportunity | null>(null);
  const [calculatorOpp, setCalculatorOpp] = useState<DetailedOpportunity | null>(null);
  const [comparedIds, setComparedIds] = useState<string[]>([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState<boolean>(false);

  // Load Data
  const loadData = async () => {
    try {
      setLoading(true);
      const [catsRes, profRes, plansRes] = await Promise.allSettled([
        incomeApi.getCategories(),
        incomeApi.getFarmProfile(farmId),
        incomeApi.getSavedPlans(farmId),
      ]);

      if (catsRes.status === "fulfilled") setCategories(catsRes.value);
      if (profRes.status === "fulfilled") setProfile(profRes.value);
      if (plansRes.status === "fulfilled") setSavedPlans(plansRes.value);

      // Match opportunities for current farm
      const opps = await incomeApi.matchOpportunities(farmId);
      setOpportunities(opps);
      if (opps.length > 0 && !calculatorOpp) {
        setCalculatorOpp(opps[0]);
      }
    } catch (e) {
      console.error("Failed to load income opportunities", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (farmId) {
      loadData();
    }
  }, [farmId]);

  // Handle Profile Update
  const handleSaveProfile = async (updated: Partial<FarmResourceProfile>) => {
    await incomeApi.updateFarmProfile(farmId, updated);
    // Reload matched opportunities and profile
    const [newProfile, newOpps] = await Promise.all([
      incomeApi.getFarmProfile(farmId),
      incomeApi.matchOpportunities(farmId, updated),
    ]);
    setProfile(newProfile);
    setOpportunities(newOpps);
  };

  // Handle Plan Delete
  const handleDeletePlan = async (planId: string) => {
    await incomeApi.deletePlan(farmId, planId);
    const updated = await incomeApi.getSavedPlans(farmId);
    setSavedPlans(updated);
  };

  // Compare Checkbox Toggle
  const handleToggleCompare = (id: string) => {
    setComparedIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 3) {
        alert("You can compare up to 3 opportunities at a time.");
        return prev;
      }
      return [...prev, id];
    });
  };

  // Filtered Opportunities List
  const filteredOpportunities = useMemo(() => {
    return opportunities.filter((opp) => {
      // Category filter
      if (selectedCategory !== "all" && opp.category.toUpperCase() !== selectedCategory.toUpperCase()) {
        return false;
      }

      // Budget filter
      const minCost = opp.setup_investment_range?.min_inr ?? 0;
      if (selectedBudgetTier === "zero" && minCost > 0) return false;
      if (selectedBudgetTier === "low" && (minCost === 0 || minCost > 25000)) return false;
      if (selectedBudgetTier === "mid" && (minCost <= 25000 || minCost > 100000)) return false;
      if (selectedBudgetTier === "high" && minCost <= 100000) return false;

      // Water filter
      if (selectedWaterFilter !== "all" && opp.water_requirement.toLowerCase() !== selectedWaterFilter.toLowerCase()) {
        return false;
      }

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesName = opp.name.toLowerCase().includes(q);
        const matchesDesc = opp.farmer_friendly_description.toLowerCase().includes(q);
        const matchesCat = opp.category.toLowerCase().includes(q);
        if (!matchesName && !matchesDesc && !matchesCat) return false;
      }

      return true;
    });
  }, [opportunities, selectedCategory, selectedBudgetTier, selectedWaterFilter, searchQuery]);

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* ── 1. Header & Farm Snapshot ── */}
      <IncomeHeader
        farmName={currentFarm?.name}
        totalAcres={currentFarm?.calculated_area_acres}
        profile={profile}
        onOpenProfileDrawer={() => setIsDrawerOpen(true)}
      />

      {/* ── 2. Primary Navigation Tabs ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3">
        <div className="flex flex-wrap gap-1.5 sm:gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("catalog")}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-extrabold transition-all sm:text-sm ${
              activeTab === "catalog"
                ? "bg-forest text-white shadow-sm"
                : "border border-line bg-white text-ink hover:bg-canvas"
            }`}
          >
            <Lightbulb size={16} />
            Explore Catalogue ({opportunities.length})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("calculator")}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-extrabold transition-all sm:text-sm ${
              activeTab === "calculator"
                ? "bg-forest text-white shadow-sm"
                : "border border-line bg-white text-ink hover:bg-canvas"
            }`}
          >
            <Calculator size={16} />
            My Farm Calculator
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("plans")}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-extrabold transition-all sm:text-sm ${
              activeTab === "plans"
                ? "bg-forest text-white shadow-sm"
                : "border border-line bg-white text-ink hover:bg-canvas"
            }`}
          >
            <FileCheck2 size={16} />
            Saved Business Plans ({savedPlans.length})
          </button>
        </div>

        {comparedIds.length > 0 && (
          <Button
            type="button"
            size="sm"
            variant="secondary"
            onClick={() => setIsCompareModalOpen(true)}
            className="font-extrabold text-xs"
          >
            <GitCompareArrows size={14} className="text-leaf" />
            Compare Selected ({comparedIds.length})
          </Button>
        )}
      </div>

      {/* ── 3. Tab Contents ── */}
      {activeTab === "catalog" && (
        <div className="space-y-6">
          {/* Category Filter Pills */}
          <div className="space-y-2">
            <span className="block text-[11px] font-bold uppercase tracking-wider text-muted">
              Select Diversification Category
            </span>
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
              <button
                type="button"
                onClick={() => setSelectedCategory("all")}
                className={`shrink-0 rounded-xl px-3.5 py-1.5 text-xs font-extrabold transition-all ${
                  selectedCategory === "all"
                    ? "bg-forest text-white shadow-sm"
                    : "border border-line bg-white text-ink hover:bg-canvas"
                }`}
              >
                All Categories ({opportunities.length})
              </button>
              {categories.map((c) => (
                <button
                  key={c.key}
                  type="button"
                  onClick={() => setSelectedCategory(c.key)}
                  className={`shrink-0 rounded-xl px-3.5 py-1.5 text-xs font-extrabold transition-all ${
                    selectedCategory.toUpperCase() === c.key.toUpperCase()
                      ? "bg-forest text-white shadow-sm"
                      : "border border-line bg-white text-ink hover:bg-canvas"
                  }`}
                >
                  {c.name} {c.count > 0 && `(${c.count})`}
                </button>
              ))}
            </div>
          </div>

          {/* Secondary Filters & Search Bar */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-line bg-white p-3.5 text-xs">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
              <input
                type="text"
                placeholder="Search enterprises (e.g., Poultry, Capsicum, Honey, Compost)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-line bg-canvas pl-9 pr-3 py-2 text-xs font-medium text-ink focus:border-forest focus:outline-none"
              />
            </div>

            {/* Budget Filter */}
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-muted shrink-0">Budget:</span>
              <select
                value={selectedBudgetTier}
                onChange={(e) => setSelectedBudgetTier(e.target.value)}
                className="rounded-xl border border-line bg-canvas px-2.5 py-1.5 text-xs font-semibold text-ink focus:border-forest focus:outline-none"
              >
                <option value="all">Any Budget</option>
                <option value="zero">₹0 (Zero Cash Only)</option>
                <option value="low">Under ₹25,000</option>
                <option value="mid">₹25,000 – ₹1,00,000</option>
                <option value="high">Above ₹1,00,000</option>
              </select>
            </div>

            {/* Water Filter */}
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-muted shrink-0">Water:</span>
              <select
                value={selectedWaterFilter}
                onChange={(e) => setSelectedWaterFilter(e.target.value)}
                className="rounded-xl border border-line bg-canvas px-2.5 py-1.5 text-xs font-semibold text-ink focus:border-forest focus:outline-none"
              >
                <option value="all">All Water Requirements</option>
                <option value="none">Zero / None</option>
                <option value="low">Low Need</option>
                <option value="moderate">Moderate Need</option>
                <option value="high">High Need (Pond / Perennial)</option>
              </select>
            </div>
          </div>

          {/* Opportunities Cards Grid */}
          {loading ? (
            <div className="py-24 text-center text-xs text-muted">
              Matching diversification opportunities against your farm resources...
            </div>
          ) : filteredOpportunities.length === 0 ? (
            <div className="rounded-3xl border border-line bg-canvas py-16 text-center text-xs">
              <p className="font-bold text-ink">No opportunities match the selected filters.</p>
              <p className="mt-1 text-muted">Try clearing the search query or budget restrictions.</p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedCategory("all");
                  setSelectedBudgetTier("all");
                  setSelectedWaterFilter("all");
                  setSearchQuery("");
                }}
                className="mt-4 font-bold"
              >
                Reset All Filters
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
              {filteredOpportunities.map((opp) => (
                <OpportunityCard
                  key={opp.opportunity_id}
                  opportunity={opp}
                  isCompared={comparedIds.includes(opp.opportunity_id)}
                  onToggleCompare={handleToggleCompare}
                  onExplore={(o) => setExploredOpp(o)}
                  onCalculate={(o) => {
                    setCalculatorOpp(o);
                    setActiveTab("calculator");
                  }}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "calculator" && (
        <div className="space-y-6">
          {/* Opportunity Selector Dropdown */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-line bg-white p-4">
            <div>
              <span className="block text-[11px] font-bold text-muted uppercase tracking-wider">
                Select Enterprise to Simulate
              </span>
              <p className="text-xs text-muted">
                Choose an enterprise below to test custom scale, operating expenses, and market prices.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={calculatorOpp?.opportunity_id ?? ""}
                onChange={(e) => {
                  const found = opportunities.find((o) => o.opportunity_id === e.target.value);
                  if (found) setCalculatorOpp(found);
                }}
                className="w-full sm:w-auto rounded-xl border border-line bg-canvas px-3 py-2 text-xs font-bold text-ink focus:border-forest focus:outline-none"
              >
                {opportunities.map((o) => (
                  <option key={o.opportunity_id} value={o.opportunity_id}>
                    {o.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {calculatorOpp && (
            <ScenarioCalculator
              opportunity={calculatorOpp}
              farmId={farmId}
              onPlanSaved={() => {
                incomeApi.getSavedPlans(farmId).then((res) => setSavedPlans(res));
              }}
            />
          )}
        </div>
      )}

      {activeTab === "plans" && (
        <SavedPlansView
          plans={savedPlans}
          onDeletePlan={handleDeletePlan}
          onSelectPlanToRecalculate={(oppId) => {
            const found = opportunities.find((o) => o.opportunity_id === oppId);
            if (found) setCalculatorOpp(found);
            setActiveTab("calculator");
          }}
          onExploreCatalogue={() => setActiveTab("catalog")}
        />
      )}

      {/* ── 4. Floating Compare Pill Bar ── */}
      {comparedIds.length > 0 && (
        <div className="fixed bottom-6 right-6 z-40 flex items-center gap-3 rounded-2xl border border-forest bg-forest px-4 py-3 text-white shadow-xl">
          <GitCompareArrows size={18} />
          <span className="text-xs font-bold">
            {comparedIds.length} enterprise{comparedIds.length > 1 ? "s" : ""} selected for comparison
          </span>
          <Button
            type="button"
            size="sm"
            onClick={() => setIsCompareModalOpen(true)}
            className="rounded-xl bg-white text-forest font-extrabold hover:bg-[#edf5ed] text-xs h-8 px-3"
          >
            Compare Now
          </Button>
          <button
            type="button"
            onClick={() => setComparedIds([])}
            className="text-[11px] text-white/80 hover:text-white underline ml-1"
          >
            Clear
          </button>
        </div>
      )}

      {/* ── 5. Modals ── */}
      <FarmerResourceDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        profile={profile}
        totalFarmAcres={currentFarm?.calculated_area_acres ?? 2.0}
        onSaveProfile={handleSaveProfile}
      />

      <OpportunityDetailModal
        opportunity={exploredOpp}
        onClose={() => setExploredOpp(null)}
        onOpenCalculator={(o) => {
          setCalculatorOpp(o);
          setActiveTab("calculator");
        }}
        onToggleCompare={handleToggleCompare}
        isCompared={exploredOpp ? comparedIds.includes(exploredOpp.opportunity_id) : false}
      />

      <OpportunityCompareModal
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
        selectedIds={comparedIds}
        allocatedAcres={profile?.available_diversification_acres ?? 0.5}
        availableBudget={profile?.available_investment_inr ?? 50000}
        onSelectForCalculate={(oppId) => {
          const found = opportunities.find((o) => o.opportunity_id === oppId);
          if (found) setCalculatorOpp(found);
          setActiveTab("calculator");
        }}
      />
    </div>
  );
}
